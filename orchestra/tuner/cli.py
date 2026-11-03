"""Subcommand dispatcher for `orchestra verify`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestra.canon.types import JsonObject
from orchestra.tuner.attestation import emit, verify
from orchestra.tuner.audit import AuditError, run_audit
from orchestra.tuner.authoring import AuthoringError, add_claim, freeze
from orchestra.tuner.binding import BindingError, bind_observation, recheck, unbind
from orchestra.tuner.evidence_kind import TEMPLATES
from orchestra.tuner.lint import find_claim_findings, find_new_skips, find_no_assert
from orchestra.tuner.manifest import ManifestError
from orchestra.tuner.observation import list_observations, maybe_record_verdict_observation
from orchestra.tuner.oracle_red import is_assertion_level_red
from orchestra.tuner.verdict import run_verdict


def _read_json(path: str | None) -> JsonObject:
    if path is None or path == "-":
        body: JsonObject = json.load(sys.stdin)
        return body
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    return body


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestra verify",
        description="Verdict, attestation, and witness lint.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    verdict = sub.add_parser(
        "verdict",
        help="Re-execute frozen oracle tests at two revisions",
    )
    verdict.add_argument(
        "--cwd",
        default=None,
        help="Git repository (default: process cwd)",
    )
    verdict.add_argument("--at", required=True, help="Revision where oracle tests must pass")
    verdict.add_argument(
        "--base",
        default=None,
        help="Revision where oracle tests must fail on an assertion (default: merge-base with main)",
    )
    verdict.add_argument(
        "--provenance",
        action="store_true",
        help="Also require git provenance: oracle lands first, oracle-only commit, distinct signers",
    )
    verdict.add_argument("claim_ids", nargs="+", metavar="CLAIM", help="Claim ids to judge")

    template = sub.add_parser(
        "runner-template",
        help="Print a shipped runner template argv as a JSON list",
    )
    template.add_argument("kind", choices=sorted(TEMPLATES))

    attest = sub.add_parser("attest", help="Emit or verify a signed verdict attestation")
    attest_sub = attest.add_subparsers(dest="attest_command", required=True)

    attest_emit = attest_sub.add_parser(
        "emit",
        help="Sign a verdict JSON body (stdin or --input)",
    )
    attest_emit.add_argument(
        "--key",
        required=True,
        help="SSH private key path for signing",
    )
    attest_emit.add_argument(
        "--input",
        default=None,
        help="Verdict JSON path (default: stdin)",
    )

    attest_verify = attest_sub.add_parser(
        "verify",
        help="Verify a signed attestation under an allowlist",
    )
    attest_verify.add_argument(
        "--allowlist",
        required=True,
        help="allowed_signers file path",
    )
    attest_verify.add_argument(
        "--commit",
        required=True,
        help="Expected commit SHA the attestation must bind",
    )
    attest_verify.add_argument(
        "--manifest-hash",
        required=True,
        help="Expected manifest hash the attestation must bind",
    )
    attest_verify.add_argument(
        "--input",
        default=None,
        help="Attestation JSON path (default: stdin)",
    )

    lint = sub.add_parser("lint", help="Report no-assert witnesses or new skips")
    lint_sub = lint.add_subparsers(dest="lint_command", required=True)

    no_assert = lint_sub.add_parser(
        "no-assert",
        help="Report witness tests with no assert or pytest.raises",
    )
    no_assert.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="Witness test source files to scan",
    )

    new_skips = lint_sub.add_parser(
        "new-skips",
        help="Report claim witnesses skipped at head but not at base",
    )
    new_skips.add_argument(
        "--cwd",
        default=None,
        help="Git repository (default: process cwd)",
    )
    new_skips.add_argument("--base", required=True, help="Base revision")
    new_skips.add_argument("--head", required=True, help="Head revision")
    new_skips.add_argument("claim_id", metavar="CLAIM", help="Claim id whose witnesses to compare")

    lint_claims = lint_sub.add_parser(
        "claims",
        help="Report compound and trust-scoped claim text in the working-tree manifest",
    )
    lint_claims.add_argument(
        "--cwd",
        default=None,
        help="Repository root (default: process cwd)",
    )

    claim = sub.add_parser("claim", help="Author manifest claims")
    claim_sub = claim.add_subparsers(dest="claim_command", required=True)
    claim_add = claim_sub.add_parser("add", help="Append a claim to the manifest")
    claim_add.add_argument("--cwd", default=None, help="Repository root (default: process cwd)")
    claim_add.add_argument("--id", required=True, dest="claim_id", help="Claim id")
    claim_add.add_argument("--text", required=True, help="Claim text")
    claim_add.add_argument(
        "--test",
        action="append",
        default=[],
        dest="tests",
        metavar="NODE",
        help="Oracle test node id (repeatable)",
    )

    freeze_cmd = sub.add_parser(
        "freeze",
        help="Record oracle file hashes from the working tree into the manifest",
    )
    freeze_cmd.add_argument("--cwd", default=None, help="Repository root (default: process cwd)")
    freeze_cmd.add_argument(
        "claim_ids", nargs="*", metavar="CLAIM", help="Claim ids (default: all)"
    )

    audit = sub.add_parser(
        "audit",
        help="Advisory: label diff blocks and optionally plant mutants",
    )
    audit.add_argument(
        "--cwd",
        default=None,
        help="Git repository (default: process cwd)",
    )
    audit.add_argument("--base", required=True, help="Base revision")
    audit.add_argument("--head", required=True, help="Head revision")
    audit.add_argument(
        "--test",
        action="append",
        default=[],
        dest="tests",
        metavar="NODE",
        help="Extra claim test node id (repeatable)",
    )
    audit.add_argument(
        "--mutants",
        default=None,
        help="JSON file of mutant proposals",
    )
    audit.add_argument(
        "--max-mutants",
        type=int,
        default=20,
        help="Cap how many mutants from the file are considered (default: 20)",
    )
    audit.add_argument(
        "--probes",
        default=None,
        help="Probe declaration JSON (default: .tuner/probes.json at head)",
    )

    trail = sub.add_parser(
        "trail",
        help="List evidence-observations from the artifact store as JSON",
    )
    trail.add_argument(
        "--cwd",
        default=None,
        help="Repository root (default: process cwd)",
    )
    trail.add_argument(
        "--claim",
        default=None,
        help="Only observations that reference this claim id",
    )
    trail.add_argument(
        "--technique",
        default=None,
        help="Only observations with this technique name",
    )

    bind = sub.add_parser(
        "bind",
        help="Attach an observation to a claim under pinned revisions",
    )
    bind.add_argument(
        "--cwd",
        default=None,
        help="Repository root (default: process cwd)",
    )
    bind.add_argument("--observation", required=True, help="Observation record id")
    bind.add_argument("--claim", required=True, help="Claim id the observation earns")
    bind.add_argument("--base", required=True, help="Pinned base revision")
    bind.add_argument("--head", required=True, help="Pinned head revision")

    unbind_cmd = sub.add_parser(
        "unbind",
        help="Retire a binding so the observation no longer earns the claim",
    )
    unbind_cmd.add_argument(
        "--cwd",
        default=None,
        help="Repository root (default: process cwd)",
    )
    unbind_cmd.add_argument("--id", required=True, help="Binding record id")

    recheck_cmd = sub.add_parser(
        "recheck",
        help="Re-judge a claim under its active binding pins",
    )
    recheck_cmd.add_argument(
        "--cwd",
        default=None,
        help="Repository root (default: process cwd)",
    )
    recheck_cmd.add_argument("--claim", required=True, help="Claim id to re-judge")

    assertion_red = sub.add_parser(
        "assertion-red",
        help="Classify whether a check-run JSON is assertion-level red (exit 0/1)",
    )
    assertion_red.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Check-run JSON path (default: stdin)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "verdict":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            payload = run_verdict(
                work, args.at, args.base, args.claim_ids, provenance=args.provenance
            )
        except ManifestError as exc:
            print(exc, file=sys.stderr)
            return 2
        print(json.dumps(payload, separators=(",", ":")))
        result = payload["result"]
        if not isinstance(result, str):
            raise TypeError("verdict result must be a string")
        maybe_record_verdict_observation(
            work,
            at=args.at,
            base=args.base,
            claim_ids=args.claim_ids,
            result=result,
        )
        return 0 if result == "pass" else 1
    if args.command == "trail":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            items = list_observations(work, claim=args.claim, technique=args.technique)
        except Exception as exc:
            print(exc, file=sys.stderr)
            return 2
        print(json.dumps(items, separators=(",", ":")))
        return 0
    if args.command == "bind":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            record = bind_observation(
                work,
                observation_id=args.observation,
                claim_id=args.claim,
                base_rev=args.base,
                head_rev=args.head,
            )
        except BindingError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(json.dumps(record, separators=(",", ":")))
        return 0
    if args.command == "unbind":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            body = unbind(work, args.id)
        except BindingError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(json.dumps(body, separators=(",", ":")))
        return 0
    if args.command == "recheck":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            payload = recheck(work, args.claim)
        except BindingError as exc:
            print(exc, file=sys.stderr)
            return 1
        except ManifestError as exc:
            print(exc, file=sys.stderr)
            return 2
        print(json.dumps(payload, separators=(",", ":")))
        return 0 if payload.get("result") == "pass" else 1
    if args.command == "assertion-red":
        try:
            record = _read_json(args.path)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0 if is_assertion_level_red(record) else 1
    if args.command == "claim":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            add_claim(work, args.claim_id, args.text, args.tests)
        except AuthoringError as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0
    if args.command == "freeze":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            freeze(work, args.claim_ids)
        except AuthoringError as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0
    if args.command == "runner-template":
        print(json.dumps(list(TEMPLATES[args.kind]), separators=(",", ":")))
        return 0
    if args.command == "audit":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        try:
            payload = run_audit(
                work,
                args.base,
                args.head,
                extra_tests=args.tests,
                mutants_path=args.mutants,
                max_mutants=args.max_mutants,
                probes_path=args.probes,
            )
        except (AuditError, ManifestError) as exc:
            print(exc, file=sys.stderr)
            return 2
        print(json.dumps(payload, separators=(",", ":")))
        return 0
    if args.command == "attest":
        if args.attest_command == "emit":
            body = _read_json(args.input)
            signed = emit(body, key_path=args.key)
            print(json.dumps(signed, separators=(",", ":")))
            return 0
        if args.attest_command == "verify":
            attestation = _read_json(args.input)
            allow = Path(args.allowlist).read_bytes()
            ok, reason = verify(
                attestation,
                allow,
                expected_commit=args.commit,
                expected_manifest_hash=args.manifest_hash,
            )
            if not ok:
                print(reason, file=sys.stderr)
                return 1
            return 0
        parser.error(f"unknown attest command {args.attest_command!r}")
    if args.command == "lint":
        if args.lint_command == "no-assert":
            findings = find_no_assert([Path(p) for p in args.paths])
            for item in findings:
                print(item)
            return 1 if findings else 0
        if args.lint_command == "new-skips":
            work = Path(args.cwd) if args.cwd else Path.cwd()
            findings = find_new_skips(work, args.base, args.head, claim_id=args.claim_id)
            for item in findings:
                print(item)
            return 1 if findings else 0
        if args.lint_command == "claims":
            work = Path(args.cwd) if args.cwd else Path.cwd()
            try:
                findings = find_claim_findings(work)
            except (OSError, ValueError) as exc:
                print(exc, file=sys.stderr)
                return 2
            for item in findings:
                print(item)
            return 1 if findings else 0
        parser.error(f"unknown lint command {args.lint_command!r}")
    parser.error(f"unknown command {args.command!r}")
    return 2
