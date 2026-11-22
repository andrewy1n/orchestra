"""Argument parsers for the conductor verbs."""

from __future__ import annotations

import argparse
from typing import Protocol

from orchestra.conductor.cli.check import add_check_parser
from orchestra.conductor.cli.workflow_commands import add_workflow_parser


class SubparserGroup(Protocol):
    def add_parser(
        self, name: str, *, help: str, description: str | None = None
    ) -> argparse.ArgumentParser: ...


def _add_suite_job_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_run_id: bool = False,
) -> None:
    """Arguments shared by suite job commands."""
    parser.add_argument("--phase", required=True, help="Phase slug")
    parser.add_argument(
        "--cwd",
        default=None,
        help="Phase worktree (default: process cwd)",
    )
    parser.add_argument(
        "--phase-head",
        default=None,
        help="Phase head revision (default: git HEAD in --cwd)",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Suite job label (default: orchestra-suite-<phase>)",
    )
    if include_run_id:
        parser.add_argument(
            "--run-id",
            default=None,
            help="Select this immutable run instead of the current run",
        )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow recording a pass on a dirty tree (revision=dirty + diff_sha256)",
    )


def add_parsers(sub: SubparserGroup) -> None:
    add_check_parser(sub)
    add_workflow_parser(sub)
    _add_wave_task_parsers(sub)
    _add_land_close_parsers(sub)
    review_brief = sub.add_parser(
        "review-brief",
        help=(
            "Build the phase-end reviewer brief from allowed store records "
            "and git diff <base>..<phase-head>"
        ),
    )
    review_brief.add_argument(
        "--cwd",
        default=None,
        help="Worktree the diff comes from (default: process cwd)",
    )
    review_brief.add_argument(
        "--base",
        default="main",
        help="Diff base revision (default: main)",
    )
    review_brief.add_argument(
        "--phase-head",
        default="HEAD",
        help="Phase head revision (default: HEAD)",
    )
    review_brief.add_argument(
        "--phase",
        default=None,
        help="Include records for this phase only",
    )
    review_brief.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )
    review_brief.add_argument(
        "--out",
        default="-",
        help="Brief path, or '-' for stdout (default)",
    )

    analyze = sub.add_parser(
        "analyze",
        help="Check a phase's specification, design, work-items, and acceptances for consistency",
    )
    analyze.add_argument("phase", help="Phase slug")
    analyze.add_argument(
        "--stage",
        choices=("spec", "design", "plan", "close"),
        default="plan",
        help="Checks to run (default: plan)",
    )
    analyze.add_argument("--json", action="store_true", help="Print one JSON object")
    analyze.add_argument(
        "--cwd",
        default=None,
        help="Directory the store is resolved from (default: process cwd)",
    )
    analyze.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )

    gate_parser = sub.add_parser(
        "gate",
        help="Check the phase gate; exit 1 and name each missing term when it does not hold",
    )
    gate_parser.add_argument("phase", help="Phase slug")
    gate_parser.add_argument("--json", action="store_true", help="Print one JSON object")
    gate_parser.add_argument(
        "--cwd",
        default=None,
        help="Phase worktree whose HEAD the gate checks (default: the Landing worktree)",
    )
    gate_parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd, else cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )

    suite_parser = sub.add_parser(
        "suite",
        help="Phase suite: policy, start, poll, collect, cancel, record",
    )
    suite_sub = suite_parser.add_subparsers(dest="action", required=True)

    suite_policy = suite_sub.add_parser(
        "policy",
        help="Print the configured orchestra.toml suite policy as JSON",
    )
    suite_policy.add_argument("--cwd", default=None, help="Worktree (default: cwd)")

    suite_start = suite_sub.add_parser(
        "start",
        help="Start the configured suite in a detached worker process",
    )
    _add_suite_job_arguments(suite_start)
    suite_start.add_argument(
        "--command",
        dest="suite_command",
        default=None,
        help="Override the configured suite command",
    )
    suite_start.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Stop the suite command after this many seconds",
    )
    suite_poll = suite_sub.add_parser(
        "poll",
        help="Return the suite result when the background job finished, else 'running'",
    )
    _add_suite_job_arguments(suite_poll, include_run_id=True)

    suite_collect = suite_sub.add_parser(
        "collect",
        help="Collect the finished suite result (exit code, log, failing node ids)",
    )
    _add_suite_job_arguments(suite_collect, include_run_id=True)

    suite_record = suite_sub.add_parser(
        "record",
        help="Collect a finished suite and write its tuner:check-run",
    )
    _add_suite_job_arguments(suite_record, include_run_id=True)
    suite_record.add_argument(
        "--effort",
        required=True,
        help="Effort/focus the check-run belongs to",
    )
    suite_cancel = suite_sub.add_parser(
        "cancel",
        help="Request cancellation of one selected suite run",
    )
    _add_suite_job_arguments(suite_cancel)
    suite_cancel.add_argument(
        "--run-id",
        required=True,
        help="Immutable run id returned by suite start",
    )
    suite_record.add_argument(
        "--criterion-id",
        default=None,
        help="Criterion id (default: <phase>-suite)",
    )
    suite_record.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def _add_wave_task_parsers(sub: SubparserGroup) -> None:
    wave = sub.add_parser("wave", help="Start and end the waves of a phase")
    wave_sub = wave.add_subparsers(dest="action", required=True)
    wave_start = wave_sub.add_parser(
        "start",
        help="Cut task branches and worktrees for the next ready wave and mark it in progress",
    )
    wave_start.add_argument("phase", help="Phase slug")
    wave_start.add_argument("--json", action="store_true", help="Print one JSON object")
    wave_start.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    wave_start.add_argument("--store", default=None, metavar="DIR", help="Store repo root")

    wave_end = wave_sub.add_parser(
        "end", help="Merge each passing task branch into the phase branch in task-slug order"
    )
    wave_end.add_argument("phase", help="Phase slug")
    wave_end.add_argument("--json", action="store_true", help="Print one JSON object")
    wave_end.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    wave_end.add_argument("--store", default=None, metavar="DIR", help="Store repo root")

    wave_resolve = wave_sub.add_parser(
        "resolve",
        help="Finish a conflicted task merge once both tasks' work is kept",
    )
    wave_resolve.add_argument("phase", help="Phase slug")
    wave_resolve.add_argument("task", help="Task slug whose merge conflicted")
    wave_resolve.add_argument("--json", action="store_true", help="Print one JSON object")
    wave_resolve.add_argument(
        "--cwd", default=None, help="Directory inside the repo (default: cwd)"
    )
    wave_resolve.add_argument("--store", default=None, metavar="DIR", help="Store repo root")

    task = sub.add_parser("task", help="Manage one task")
    task_sub = task.add_subparsers(dest="action", required=True)
    task_redispatch_parser = task_sub.add_parser(
        "redispatch", help="Start a new measured dispatch for an in-progress task"
    )
    task_redispatch_parser.add_argument("task", help="Work-item subject")
    task_redispatch_parser.add_argument(
        "--expected-revision", required=True, help="Exact current work-item revision"
    )
    task_redispatch_parser.add_argument("--json", action="store_true", help="Print one JSON object")
    task_redispatch_parser.add_argument(
        "--cwd", default=None, help="Directory inside the repo (default: cwd)"
    )
    task_redispatch_parser.add_argument(
        "--store", default=None, metavar="DIR", help="Store repo root"
    )

    task_land = task_sub.add_parser(
        "land", help="Commit a task worktree, record its evidence, run its checks, close it"
    )
    task_land.add_argument("task", nargs="?", help="Work-item subject")
    task_land.add_argument("--evidence", default=None, help="Evidence JSON file")
    task_land.add_argument("--schema", action="store_true", help="Print the evidence JSON schema")
    task_land.add_argument("--json", action="store_true", help="Print one JSON object")
    task_land.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    task_land.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _add_land_close_parsers(sub: SubparserGroup) -> None:
    close_batch = sub.add_parser(
        "close-batch",
        help="Build NDJSON apply batch that closes a work-item",
    )
    close_batch.add_argument(
        "--input",
        default="-",
        help="close-request JSON path, or '-' for stdin (default)",
    )
    close_batch.add_argument(
        "--out",
        default="-",
        help="NDJSON output path, or '-' for stdout (default)",
    )
    close_batch.add_argument(
        "--cwd",
        default=None,
        help="git cwd for red-first ancestry checks (default: process cwd)",
    )
    close_batch.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help="Store repo root (default: $ORCHESTRA_STORE, then resolve from the process cwd)",
    )

    land = sub.add_parser(
        "land",
        help="Run the phase gate, then open the configured pull request and wait for CI",
    )
    land.add_argument("--phase", required=True, help="Phase slug")
    land.add_argument("--cwd", default=None, help="Phase worktree (default: process cwd)")
    land.add_argument("--base", default="main", help="Pull request base branch")
    land.add_argument("--remote", default="origin", help="Git remote to publish")
    land.add_argument(
        "--poll-interval", type=float, default=10, help="CI polling interval in seconds"
    )
    land.add_argument("--timeout", type=float, default=1800, help="Maximum CI wait in seconds")
    land.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )

    close = sub.add_parser(
        "close",
        help=(
            "After the pull request merges, remove the phase worktrees and branches "
            "and close the phase"
        ),
        description=(
            "After the pull request merges, close removes the worktrees and branches of the "
            "phase and closes the phase. Run it from the main checkout."
        ),
    )
    close.add_argument("--phase", default=None, help="Phase slug")
    close.add_argument(
        "--all", action="store_true", help="Close every landed phase that still has work to close"
    )
    close.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    close.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )
