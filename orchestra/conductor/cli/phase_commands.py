"""Handlers for `orchestra gate`, `analyze` and `review-brief`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.project_config import ProjectConfigError
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import gate
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)
from orchestra.conductor.phase_analysis import analyze_in_store
from orchestra.conductor.review_brief import build_review_brief


def run_analyze(args: argparse.Namespace) -> int:
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.READ)
        report = analyze_in_store(workspace.open(), workspace.root, args.phase, args.stage)
    except StoreNotReady as exc:
        print(f"orchestra analyze: {args.phase}: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError, StoreBindingError, StoreError, ProjectConfigError) as exc:
        print(f"orchestra analyze: {args.phase}: {exc}", file=sys.stderr)
        return 2
    if report is None:
        print(f"orchestra analyze: phase {args.phase!r} not found", file=sys.stderr)
        return 2
    if args.json:
        print_json(
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


def run_gate(args: argparse.Namespace) -> int:
    head_worktree = command_dir(args).resolve() if args.cwd else None
    start = head_worktree or Path.cwd()
    try:
        workspace = resolve_workspace(args.store, start, Access.READ)
        terms = gate.gate_terms(workspace.open(), args.phase, head_worktree=head_worktree)
    except StoreNotReady as exc:
        print(f"orchestra gate: {args.phase}: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (LookupError, OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        print(f"orchestra gate: {args.phase}: {exc}", file=sys.stderr)
        return 2
    missing = gate.missing_terms(terms)
    if args.json:
        print_json(
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


def run_review_brief(args: argparse.Namespace) -> int:
    work = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, work, Access.READ)
        brief = build_review_brief(
            workspace.open(),
            work,
            base=args.base,
            phase_head=args.phase_head,
            phase=args.phase,
        )
    except StoreNotReady as exc:
        print(f"orchestra review-brief: {not_ready_message(exc, work)}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError, StoreBindingError) as exc:
        print(f"orchestra review-brief: {exc}", file=sys.stderr)
        return 2
    if brief.refusal:
        print(f"orchestra review-brief: {brief.refusal}", file=sys.stderr)
        return 2
    if args.out == "-":
        print(brief.text, end="" if brief.text.endswith("\n") else "\n")
        return 0
    destination = Path(args.out).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(brief.text, encoding="utf-8")
    print(destination)
    return 0
