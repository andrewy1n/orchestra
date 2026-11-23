"""Command list for `orchestra verify` and `orchestra plugins`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from orchestra.canon.extensions import PLUGIN_GROUPS, list_plugins
from orchestra.canon.types import JsonObject
from orchestra.canon.workspace import Access, open_for_command
from orchestra.tools import command_kit
from orchestra.tools.command_kit import Command, CommandError
from orchestra.tuner import verify_plugins
from orchestra.tuner.authoring.audit import AuditError, AuditTrailError, run_audit
from orchestra.tuner.authoring.authoring import AuthoringError, add_claim, freeze
from orchestra.tuner.authoring.lint import find_claim_findings, find_new_skips, find_no_assert
from orchestra.tuner.authoring.observation import (
    list_observations,
    maybe_record_verdict_observation,
)
from orchestra.tuner.authoring.oracle_red import is_assertion_level_red
from orchestra.tuner.evidence.binding import BindingError, bind_observation, recheck, unbind
from orchestra.tuner.evidence.signing.attestation import emit, verify
from orchestra.tuner.evidence.verdict import run_verdict
from orchestra.tuner.plugins.evidence_kind import TEMPLATES
from orchestra.tuner.plugins.manifest import ManifestError

__all__ = ["commands", "main"]


def _read_json(path: str | None) -> JsonObject:
    if path is None or path == "-":
        body: JsonObject = json.load(sys.stdin)
        return body
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    return body


def _work(args: argparse.Namespace) -> Path:
    return Path(args.cwd) if args.cwd else Path.cwd()


def _add_cwd(
    parser: argparse.ArgumentParser, help: str = "Repository root (default: process cwd)"
) -> None:
    parser.add_argument("--cwd", default=None, help=help)


def _add_require_trail(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--require-trail",
        action="store_true",
        help="Return an operational error if the observation trail cannot be saved",
    )


def _configure_plugins_list(listing: argparse.ArgumentParser) -> None:
    listing.add_argument("--scope", choices=tuple(PLUGIN_GROUPS), default=None)
    listing.add_argument("--format", choices=("table", "json"), default="table")


def _plugins_list(args: argparse.Namespace) -> int:
    descriptors = sorted(list_plugins(args.scope), key=lambda item: (item.scope, item.plugin_id))
    if args.format == "json":
        print(json.dumps([asdict(item) for item in descriptors], sort_keys=True))
        return 0
    print("scope\tid\tapi\tdistribution\tversion\ttarget")
    for descriptor in descriptors:
        print(
            "\t".join(
                (
                    descriptor.scope,
                    descriptor.plugin_id,
                    descriptor.api_version,
                    descriptor.distribution,
                    descriptor.version,
                    descriptor.target,
                )
            )
        )
    return 0


def _configure_verdict(verdict: argparse.ArgumentParser) -> None:
    _add_cwd(verdict, "Git repository (default: process cwd)")
    verdict.add_argument("--at", required=True, help="Revision where oracle tests must pass")
    verdict.add_argument(
        "--base",
        default=None,
        help="Revision where oracle tests must fail on an assertion (default: common ancestor with main)",
    )
    verdict.add_argument(
        "--provenance",
        action="store_true",
        help="Also require git provenance: oracle lands first, oracle-only commit, distinct signers",
    )
    verdict.add_argument("claim_ids", nargs="+", metavar="CLAIM", help="Claim ids to judge")
    _add_require_trail(verdict)


def _verdict(args: argparse.Namespace) -> int:
    work = _work(args)
    try:
        payload = run_verdict(work, args.at, args.base, args.claim_ids, provenance=args.provenance)
    except ManifestError as exc:
        raise CommandError(str(exc), 2) from exc
    command_kit.emit_json(payload, compact=True)
    result = payload["result"]
    if not isinstance(result, str):
        raise TypeError("verdict result must be a string")
    recorded = maybe_record_verdict_observation(
        work, at=args.at, base=args.base, claim_ids=args.claim_ids, result=result
    )
    if args.require_trail and not recorded:
        raise CommandError("required observation trail could not be persisted", 2)
    return 0 if result == "pass" else 1


def _configure_runner_template(template: argparse.ArgumentParser) -> None:
    template.add_argument("kind", choices=sorted(TEMPLATES))


def _runner_template(args: argparse.Namespace) -> int:
    command_kit.emit_json(list(TEMPLATES[args.kind]), compact=True)
    return 0


def _configure_attest_emit(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--key", required=True, help="SSH private key path for signing")
    parser.add_argument("--input", default=None, help="Verdict JSON path (default: stdin)")


def _attest_emit(args: argparse.Namespace) -> int:
    signed = emit(_read_json(args.input), key_path=args.key)
    command_kit.emit_json(signed, compact=True)
    return 0


def _configure_attest_verify(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--allowlist", required=True, help="allowed_signers file path")
    parser.add_argument(
        "--commit", required=True, help="Expected commit SHA the attestation must bind"
    )
    parser.add_argument(
        "--manifest-hash", required=True, help="Expected manifest hash the attestation must bind"
    )
    parser.add_argument("--input", default=None, help="Attestation JSON path (default: stdin)")


def _attest_verify(args: argparse.Namespace) -> int:
    attestation = _read_json(args.input)
    allow = Path(args.allowlist).read_bytes()
    ok, reason = verify(
        attestation,
        allow,
        expected_commit=args.commit,
        expected_manifest_hash=args.manifest_hash,
    )
    if not ok:
        raise CommandError(reason, 1)
    return 0


def _configure_lint_no_assert(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "paths", nargs="+", metavar="PATH", help="Witness test source files to scan"
    )


def _report(findings: list[str]) -> int:
    for item in findings:
        print(item)
    return 1 if findings else 0


def _lint_no_assert(args: argparse.Namespace) -> int:
    return _report(find_no_assert([Path(p) for p in args.paths]))


def _configure_lint_new_skips(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser, "Git repository (default: process cwd)")
    parser.add_argument("--base", required=True, help="Base revision")
    parser.add_argument("--head", required=True, help="Head revision")
    parser.add_argument("claim_id", metavar="CLAIM", help="Claim id whose witnesses to compare")


def _lint_new_skips(args: argparse.Namespace) -> int:
    return _report(find_new_skips(_work(args), args.base, args.head, claim_id=args.claim_id))


def _lint_claims(args: argparse.Namespace) -> int:
    try:
        findings = find_claim_findings(_work(args))
    except (OSError, ValueError) as exc:
        raise CommandError(str(exc), 2) from exc
    return _report(findings)


def _configure_claim_add(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--id", required=True, dest="claim_id", help="Claim id")
    parser.add_argument("--text", required=True, help="Claim text")
    parser.add_argument(
        "--test",
        action="append",
        default=[],
        dest="tests",
        metavar="NODE",
        help="Oracle test node id (repeatable)",
    )


def _claim_add(args: argparse.Namespace) -> int:
    try:
        add_claim(_work(args), args.claim_id, args.text, args.tests)
    except AuthoringError as exc:
        raise CommandError(str(exc), 2) from exc
    return 0


def _configure_freeze(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("claim_ids", nargs="*", metavar="CLAIM", help="Claim ids (default: all)")


def _freeze(args: argparse.Namespace) -> int:
    try:
        freeze(_work(args), args.claim_ids)
    except AuthoringError as exc:
        raise CommandError(str(exc), 2) from exc
    return 0


def _configure_audit(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser, "Git repository (default: process cwd)")
    parser.add_argument("--base", required=True, help="Base revision")
    parser.add_argument("--head", required=True, help="Head revision")
    parser.add_argument(
        "--test",
        action="append",
        default=[],
        dest="tests",
        metavar="NODE",
        help="Extra claim test node id (repeatable)",
    )
    parser.add_argument("--mutants", default=None, help="JSON file of mutant proposals")
    parser.add_argument(
        "--max-mutants",
        type=int,
        default=20,
        help="Cap how many mutants from the file are considered (default: 20)",
    )
    parser.add_argument(
        "--probes",
        default=None,
        help="Probe declaration JSON (default: .tuner/probes.json at head)",
    )
    _add_require_trail(parser)


def _audit(args: argparse.Namespace) -> int:
    try:
        payload = run_audit(
            _work(args),
            args.base,
            args.head,
            extra_tests=args.tests,
            mutants_path=args.mutants,
            max_mutants=args.max_mutants,
            probes_path=args.probes,
            require_trail=args.require_trail,
        )
    except AuditTrailError as exc:
        command_kit.emit_json(exc.report, compact=True)
        raise CommandError(str(exc), 2) from exc
    except (AuditError, ManifestError) as exc:
        raise CommandError(str(exc), 2) from exc
    command_kit.emit_json(payload, compact=True)
    return 0


def _configure_trail(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument(
        "--claim", default=None, help="Only observations that reference this claim id"
    )
    parser.add_argument(
        "--technique", default=None, help="Only observations with this technique name"
    )


def _trail(args: argparse.Namespace) -> int:
    work = _work(args)
    open_for_command(work, Access.READ, store=work)
    try:
        items = list_observations(work, claim=args.claim, technique=args.technique)
    except Exception as exc:
        raise CommandError(str(exc), 2) from exc
    command_kit.emit_json(items, compact=True)
    return 0


def _configure_bind(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--observation", required=True, help="Observation record id")
    parser.add_argument("--claim", required=True, help="Claim id the observation earns")
    parser.add_argument("--base", required=True, help="Pinned base revision")
    parser.add_argument("--head", required=True, help="Pinned head revision")


def _bind(args: argparse.Namespace) -> int:
    work = _work(args)
    open_for_command(work, Access.WRITE, store=work)
    try:
        record = bind_observation(
            work,
            observation_id=args.observation,
            claim_id=args.claim,
            base_rev=args.base,
            head_rev=args.head,
        )
    except BindingError as exc:
        raise CommandError(str(exc), 1) from exc
    command_kit.emit_json(record, compact=True)
    return 0


def _configure_unbind(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--id", required=True, help="Binding record id")


def _unbind(args: argparse.Namespace) -> int:
    work = _work(args)
    open_for_command(work, Access.WRITE, store=work)
    try:
        body = unbind(work, args.id)
    except BindingError as exc:
        raise CommandError(str(exc), 1) from exc
    command_kit.emit_json(body, compact=True)
    return 0


def _configure_recheck(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--claim", required=True, help="Claim id to re-judge")


def _recheck(args: argparse.Namespace) -> int:
    work = _work(args)
    open_for_command(work, Access.WRITE, store=work)
    try:
        payload = recheck(work, args.claim)
    except BindingError as exc:
        raise CommandError(str(exc), 1) from exc
    except ManifestError as exc:
        raise CommandError(str(exc), 2) from exc
    command_kit.emit_json(payload, compact=True)
    return 0 if payload.get("result") == "pass" else 1


def _configure_assertion_red(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "path", nargs="?", default=None, help="Check-run JSON path (default: stdin)"
    )


def _assertion_red(args: argparse.Namespace) -> int:
    try:
        record = _read_json(args.path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CommandError(str(exc), 2) from exc
    return 0 if is_assertion_level_red(record) else 1


def _verify_children() -> tuple[Command, ...]:
    return (
        Command(
            "verdict",
            "Re-execute frozen oracle tests at two revisions",
            configure=_configure_verdict,
            handle=_verdict,
        ),
        Command(
            "runner-template",
            "Print a shipped runner template argv as a JSON list",
            configure=_configure_runner_template,
            handle=_runner_template,
        ),
        Command(
            "attest",
            "Emit or verify a signed verdict attestation",
            children=(
                Command(
                    "emit",
                    "Sign a verdict JSON body (stdin or --input)",
                    configure=_configure_attest_emit,
                    handle=_attest_emit,
                ),
                Command(
                    "verify",
                    "Verify a signed attestation under an allowlist",
                    configure=_configure_attest_verify,
                    handle=_attest_verify,
                ),
            ),
        ),
        Command(
            "lint",
            "Report no-assert witnesses or new skips",
            children=(
                Command(
                    "no-assert",
                    "Report witness tests with no assert or pytest.raises",
                    configure=_configure_lint_no_assert,
                    handle=_lint_no_assert,
                ),
                Command(
                    "new-skips",
                    "Report claim witnesses skipped at head but not at base",
                    configure=_configure_lint_new_skips,
                    handle=_lint_new_skips,
                ),
                Command(
                    "claims",
                    "Report compound and trust-scoped claim text in the working-tree manifest",
                    configure=_add_cwd,
                    handle=_lint_claims,
                ),
            ),
        ),
        Command(
            "claim",
            "Author manifest claims",
            children=(
                Command(
                    "add",
                    "Append a claim to the manifest",
                    configure=_configure_claim_add,
                    handle=_claim_add,
                ),
            ),
        ),
        Command(
            "freeze",
            "Record oracle file hashes from the working tree into the manifest",
            configure=_configure_freeze,
            handle=_freeze,
        ),
        Command(
            "audit",
            "Advisory: label diff blocks and optionally plant mutants",
            configure=_configure_audit,
            handle=_audit,
        ),
        Command(
            "trail",
            "List evidence-observations from the artifact store as JSON",
            configure=_configure_trail,
            handle=_trail,
        ),
        Command(
            "bind",
            "Attach an observation to a claim under pinned revisions",
            configure=_configure_bind,
            handle=_bind,
        ),
        Command(
            "unbind",
            "Retire a binding so the observation no longer earns the claim",
            configure=_configure_unbind,
            handle=_unbind,
        ),
        Command(
            "recheck",
            "Re-judge a claim under its active binding pins",
            configure=_configure_recheck,
            handle=_recheck,
        ),
        Command(
            "assertion-red",
            "Classify whether a check-run JSON is assertion-level red (exit 0/1)",
            configure=_configure_assertion_red,
            handle=_assertion_red,
        ),
        verify_plugins.command(),
    )


def commands() -> list[Command]:
    return [
        Command(
            "verify",
            "Verdict, attestation, claims, audit, and evidence binding",
            passthrough=True,
            children=_verify_children(),
        ),
        Command(
            "plugins",
            "List installed plugins",
            children=(
                Command(
                    "list",
                    "List installed plugins by scope",
                    configure=_configure_plugins_list,
                    handle=_plugins_list,
                ),
            ),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra verify",
        description="Verdict, attestation, and witness lint.",
    )
    command_kit.mount(parser.add_subparsers(required=True), _verify_children(), ("verify",))
    args = parser.parse_args(argv)
    return command_kit.run(args)
