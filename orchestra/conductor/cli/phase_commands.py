"""Handlers for `orchestra gate`, `analyze` and `review-brief`."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.project_config import ProjectConfigError
from orchestra.canon.workspace import Access
from orchestra.conductor.cli.options import open_project, work_dir
from orchestra.conductor.landing import gate
from orchestra.conductor.phases.progress.phase_analysis import analyze_in_store
from orchestra.conductor.verification.review.review_brief import build_review_brief
from orchestra.conductor.verification.suite.suite import suite_refusal
from orchestra.tools.command_kit import Command, CommandError, emit_json

_STORE_HELP = (
    "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
    "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
)


def _configure_review_brief(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cwd",
        default=None,
        help="Worktree the diff comes from (default: process cwd)",
    )
    parser.add_argument(
        "--base",
        default="main",
        help="Diff base revision (default: main)",
    )
    parser.add_argument(
        "--phase-head",
        default="HEAD",
        help="Phase head revision (default: HEAD)",
    )
    parser.add_argument(
        "--phase",
        default=None,
        help="Include records for this phase only",
    )
    parser.add_argument("--store", default=None, metavar="DIR", help=_STORE_HELP)
    parser.add_argument(
        "--out",
        default="-",
        help="Brief path, or '-' for stdout (default)",
    )


def _configure_analyze(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("phase", help="Phase slug")
    parser.add_argument(
        "--stage",
        choices=("spec", "design", "plan", "close"),
        default="plan",
        help="Checks to run (default: plan)",
    )
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument(
        "--cwd",
        default=None,
        help="Directory the store is resolved from (default: process cwd)",
    )
    parser.add_argument("--store", default=None, metavar="DIR", help=_STORE_HELP)


def _configure_gate(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("phase", help="Phase slug")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument(
        "--cwd",
        default=None,
        help="Phase worktree whose HEAD the gate checks (default: the Landing worktree)",
    )
    parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd, else cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def _analyze(args: argparse.Namespace) -> int:
    start = work_dir(args)
    project = open_project(args, start, Access.READ)
    try:
        report = analyze_in_store(project, project.project_root, args.phase, args.stage)
    except (OSError, RuntimeError, StoreBindingError, StoreError, ProjectConfigError) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    if report is None:
        raise CommandError(f"phase {args.phase!r} not found")
    if args.json:
        emit_json(
            {
                "phase": report.phase,
                "stage": report.stage,
                "skipped": False,
                "findings": [f.to_dict() for f in report.findings],
            }
        )
    else:
        for f in report.findings:
            print(f"{f.severity} {f.code} {f.subject}: {f.message}")
        errors = sum(f.severity == "error" for f in report.findings)
        warnings = len(report.findings) - errors
        print(f"{args.phase} ({args.stage}): {errors} errors, {warnings} warnings")
    return 0 if report.ok else 1


def _gate(args: argparse.Namespace) -> int:
    head_worktree = work_dir(args).resolve() if args.cwd else None
    start = head_worktree or Path.cwd()
    project = open_project(args, start, Access.READ)
    try:
        terms = gate.gate_terms(project, args.phase, head_worktree=head_worktree)
    except (LookupError, OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    missing = gate.missing_terms(terms)
    if args.json:
        emit_json(
            {
                "phase": args.phase,
                "holds": not missing,
                "missing": [term.name for term in missing],
            }
        )
    elif missing:
        for line in gate.format_missing(missing):
            print(f"{args.phase}: {line}")
    else:
        print(f"{args.phase}: gate holds")
    return 1 if missing else 0


def _review_brief(args: argparse.Namespace) -> int:
    work = work_dir(args)
    project = open_project(args, work, Access.READ)
    try:
        refusal = suite_refusal(project, work, args.phase, args.phase_head) if args.phase else ""
        brief = (
            ""
            if refusal
            else build_review_brief(
                project,
                work,
                base=args.base,
                phase_head=args.phase_head,
                phase=args.phase,
            )
        )
    except (OSError, RuntimeError, StoreBindingError) as exc:
        raise CommandError(str(exc)) from exc
    if refusal:
        raise CommandError(refusal)
    if args.out == "-":
        print(brief, end="" if brief.endswith("\n") else "\n")
        return 0
    destination = Path(args.out).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(brief, encoding="utf-8")
    print(destination)
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "review-brief",
            "Build the phase-end reviewer brief from allowed store records "
            "and git diff <base>..<phase-head>",
            configure=_configure_review_brief,
            handle=_review_brief,
        ),
        Command(
            "analyze",
            "Check a phase's specification, design, work-items, and acceptances for consistency",
            configure=_configure_analyze,
            handle=_analyze,
        ),
        Command(
            "gate",
            "Check the phase gate; exit 1 and name each missing term when it does not hold",
            configure=_configure_gate,
            handle=_gate,
        ),
    ]
