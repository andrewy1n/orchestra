"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from orchestra import aa, reviewer, suite
from orchestra.aa_resolve import (
    StoreBindingError,
    project_root,
    resolve as resolve_store,
)
from orchestra.check import DEFAULT_TIMEOUT_S, git_head, run_check
from orchestra.contract import contract_path
from orchestra.project_field import STOPPED, rewrite_project_field
from orchestra.sessions import aggregate as aggregate_sessions
from orchestra.sessions import report as report_sessions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestra",
        description=(
            "orchestra CLI: checks, contracts, reviewer briefs, phase suite, "
            "and store access (shells to adaptive-artifacts)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser(
        "check",
        help="Run an acceptance verify_command and write a project:check-run",
    )
    check.add_argument("--acceptance", required=True, help="Acceptance record id")
    check.add_argument(
        "--cwd",
        default=None,
        help="Directory for git revision and verify_command (default: process cwd)",
    )
    check.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow recording a pass on a dirty tree (revision=dirty + diff_sha256)",
    )
    check.add_argument(
        "--execution-report",
        default=None,
        help="Optional execution-report id to link via informed_by",
    )
    check.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help=f"verify_command timeout in seconds (default: {DEFAULT_TIMEOUT_S:g})",
    )

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

    install = sub.add_parser(
        "install",
        help="Install orchestra payload for one or more agent hosts",
    )
    install.add_argument(
        "--only",
        action="append",
        metavar="HOST",
        default=[],
        help=(
            "Install only this provider id; repeat for more "
            "(default: detected hosts)"
        ),
    )
    install.add_argument(
        "--all",
        action="store_true",
        help="Select every provider in the matrix",
    )
    scope = install.add_mutually_exclusive_group()
    scope.add_argument(
        "--scope",
        choices=("project", "global"),
        default=None,
        help="Install into the project or the user directories",
    )
    scope.add_argument(
        "--global",
        dest="scope",
        action="store_const",
        const="global",
        help="Alias for --scope global",
    )
    install.add_argument(
        "--list",
        "-l",
        dest="list_only",
        action="store_true",
        help="Print the provider matrix with project/global detection",
    )
    install.add_argument(
        "--copy",
        action="store_true",
        help="Copy payload instead of symlinking to this checkout",
    )
    install.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and write nothing",
    )
    install.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove exactly what the adapter registered",
    )
    interactive = install.add_mutually_exclusive_group()
    interactive.add_argument(
        "--interactive",
        action="store_true",
        help="Force the host wizard even when standard input is not a TTY",
    )
    interactive.add_argument(
        "--non-interactive",
        "--yes",
        "-y",
        dest="non_interactive",
        action="store_true",
        help="Never prompt; use --only/--all or detected hosts",
    )
    install.add_argument(
        "--home",
        default=None,
        metavar="DIR",
        help="Redirect the whole install under DIR (tests, throwaway homes)",
    )

    contract = sub.add_parser(
        "contract",
        help="Print the bundled project-design contract",
    )
    contract.add_argument(
        "--path",
        action="store_true",
        help="Print the contract file path instead of its contents",
    )
    contract.add_argument(
        "--write",
        metavar="PATH",
        default=None,
        help="Write the bundled contract to PATH",
    )

    project_field = sub.add_parser(
        "project-field",
        help="Align a design file's project field with orchestra",
    )
    project_field_sub = project_field.add_subparsers(dest="action", required=True)
    rewrite = project_field_sub.add_parser(
        "rewrite",
        help="Rewrite the project field in place when it is affidavit",
    )
    rewrite.add_argument("design", help="Path to a project-design.json")
    rewrite.add_argument(
        "--json",
        action="store_true",
        help="Print the outcome as JSON instead of one word",
    )

    sessions = sub.add_parser(
        "sessions",
        help="Summarize Claude Code session transcripts",
    )
    sessions_sub = sessions.add_subparsers(dest="action", required=True)
    report = sessions_sub.add_parser(
        "report",
        help="Print one JSON summary per session transcript",
    )
    report.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Transcript root (default: ~/.claude/projects)",
    )
    report.add_argument(
        "--records",
        action="store_true",
        help="Attach matched record counts to each session",
    )
    aggregate = sessions_sub.add_parser(
        "aggregate",
        help="Print one aggregate document for a report JSONL file",
    )
    aggregate.add_argument(
        "report",
        nargs="?",
        default="-",
        help="report JSONL path, or '-' for stdin (default)",
    )

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
        "--store",
        default=None,
        metavar="DIR",
        help="Store root (default: resolve from --cwd)",
    )
    review_brief.add_argument(
        "--out",
        default="-",
        help="Brief path, or '-' for stdout (default)",
    )

    suite_parser = sub.add_parser(
        "suite",
        help="Phase suite: contracted policy, background run, collect, record",
    )
    suite_sub = suite_parser.add_subparsers(dest="action", required=True)

    suite_policy = suite_sub.add_parser(
        "policy",
        help="Print the contracted phase_gate.suite policy as JSON",
    )
    suite_policy.add_argument("--cwd", default=None, help="Worktree (default: cwd)")

    suite_start = suite_sub.add_parser(
        "start",
        help="Start the contracted suite in a detached tmux session",
    )
    _add_suite_job_arguments(suite_start)
    suite_start.add_argument(
        "--command",
        dest="suite_command",
        default=None,
        help="Override the contracted suite command",
    )

    suite_poll = suite_sub.add_parser(
        "poll",
        help="Return the suite result when the background job finished, else 'running'",
    )
    _add_suite_job_arguments(suite_poll)

    suite_collect = suite_sub.add_parser(
        "collect",
        help="Collect the finished suite result (exit code, log, failing node ids)",
    )
    _add_suite_job_arguments(suite_collect)

    suite_record = suite_sub.add_parser(
        "record",
        help="Collect a finished suite and write its project:check-run",
    )
    _add_suite_job_arguments(suite_record)
    suite_record.add_argument(
        "--effort",
        required=True,
        help="Effort/focus the check-run belongs to",
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
        help="Store root (default: resolve from --cwd)",
    )

    store = sub.add_parser(
        "store",
        help="Resolve the bound store and run adaptive-artifacts through it",
    )
    store_sub = store.add_subparsers(dest="action", required=True)
    store_path = store_sub.add_parser(
        "path",
        help="Print the resolved store path for a directory",
    )
    store_path.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_path.add_argument(
        "--json",
        action="store_true",
        help="Print the resolved root, store, contract, and binding as JSON",
    )
    store_run = store_sub.add_parser(
        "run",
        help="Run adaptive-artifacts with the resolved --root/--store/--contract",
    )
    store_run.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="adaptive-artifacts arguments, after '--'",
    )
    store_ensure = store_sub.add_parser(
        "ensure",
        help="Create .artifacts/ and write the bundled design when absent",
    )
    store_ensure.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_ensure.add_argument(
        "--json",
        action="store_true",
        help="Print the created paths and store readiness as JSON",
    )
    return parser


def _add_suite_job_arguments(parser: argparse.ArgumentParser) -> None:
    """Arguments shared by start/poll/collect/record suite jobs."""
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
        help="tmux session name (default: orchestra-suite-<phase>)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow recording a pass on a dirty tree (revision=dirty + diff_sha256)",
    )


def _cwd(args: argparse.Namespace) -> Path:
    return Path(args.cwd).expanduser() if args.cwd else Path.cwd()


def _store_root(args: argparse.Namespace, work: Path) -> Path:
    if getattr(args, "store", None):
        return Path(args.store).expanduser()
    return aa.find_store_root(work)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def _policy_document(policy: suite.SuitePolicy) -> dict[str, object]:
    return {
        "mode": policy.mode,
        "command": policy.command,
        "gate": policy.gate,
        "source_path": policy.source_path,
        "run_locally": policy.run_locally,
        "blocks_merge": policy.blocks_merge,
        "advisory": policy.advisory,
        "deferred_landing_stop": policy.deferred_landing_stop,
        "create_fix_tasks_on_fail": policy.create_fix_tasks_on_fail,
    }


def _suite_result_document(result: suite.SuiteResult) -> dict[str, object]:
    return {
        "state": result.result,
        "result": result.result,
        "revision": result.revision,
        "exit_code": result.exit_code,
        "duration_s": result.duration_s,
        "output_sha256": result.output_sha256,
        "failing_node_ids": result.failing_node_ids,
        "diff_sha256": result.diff_sha256,
        "refuse": result.refuse,
        "refuse_message": result.refuse_message,
        "skipped": result.skipped,
        "skip_reason": result.skip_reason,
    }


def _suite_exit_code(result: suite.SuiteResult) -> int:
    if result.refuse or result.result == "blocked":
        return 2
    if result.result == "fail":
        return 1
    return 0


def _suite_job(args: argparse.Namespace) -> suite.SuiteStart:
    """Rebuild the start handle from the worktree's ``.suite/`` files.

    The files are the same ones ``start_suite_background`` writes, so a
    separate CLI process can poll a job a previous process started.
    """
    work = _cwd(args).resolve()
    slug = args.phase.strip()
    name = args.session or f"orchestra-suite-{slug}"
    head = args.phase_head or git_head(work)
    log_path = work / ".suite" / f"{name}.log"
    exit_path = work / ".suite" / f"{name}.exit"
    started = time.monotonic()
    if log_path.is_file():
        started -= max(0.0, time.time() - log_path.stat().st_ctime)
    return suite.SuiteStart(
        session_name=name,
        worktree=work,
        phase_slug=slug,
        phase_head=head,
        log_path=log_path,
        exit_path=exit_path,
        started_monotonic=started,
    )


def _load_review_records(
    store_root: Path,
) -> tuple[list[dict[str, object]], list[str]]:
    """Read the reviewer-allowed kinds through adaptive-artifacts list."""
    records: list[dict[str, object]] = []
    failures: list[str] = []
    for kind in sorted(reviewer.ALLOWED_KINDS):
        result = aa.run_aa(
            "list", "--type", f"project:{kind}", "--full", root=store_root
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            failures.append(f"project:{kind}: {detail or 'list failed'}")
            continue
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            failures.append(f"project:{kind}: invalid JSON")
            continue
        rows = payload.get("records") if isinstance(payload, dict) else payload
        if isinstance(rows, list):
            records.extend(row for row in rows if isinstance(row, dict))
    if not records and failures:
        raise RuntimeError("; ".join(failures))
    return records, failures


def _cmd_review_brief(args: argparse.Namespace) -> int:
    work = _cwd(args)
    try:
        records, failures = _load_review_records(_store_root(args, work))
        phase_diff = reviewer.git_phase_diff(
            work, base=args.base, phase_head=args.phase_head
        )
        brief = reviewer.build_reviewer_brief(
            records=records,
            phase_diff=phase_diff,
            base=args.base,
            phase_head=args.phase_head,
        )
    except (OSError, RuntimeError, StoreBindingError) as exc:
        print(f"orchestra review-brief: {exc}", file=sys.stderr)
        return 2
    for failure in failures:
        print(f"orchestra review-brief: skipped {failure}", file=sys.stderr)
    if args.out == "-":
        print(brief, end="" if brief.endswith("\n") else "\n")
        return 0
    destination = Path(args.out).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(brief, encoding="utf-8")
    print(destination)
    return 0


def _cmd_suite_policy(args: argparse.Namespace) -> int:
    try:
        policy = suite.load_suite_policy(_cwd(args))
    except (OSError, RuntimeError, StoreBindingError) as exc:
        print(f"orchestra suite policy: {exc}", file=sys.stderr)
        return 2
    _print_json(_policy_document(policy))
    return 0


def _cmd_suite_start(args: argparse.Namespace) -> int:
    try:
        outcome = suite.start_suite_background(
            worktree=_cwd(args),
            phase_slug=args.phase,
            phase_head=args.phase_head,
            session_name=args.session,
            suite_command=args.suite_command,
            allow_dirty=args.allow_dirty,
        )
    except (OSError, RuntimeError, StoreBindingError, ValueError) as exc:
        print(f"orchestra suite start: {exc}", file=sys.stderr)
        return 2
    if isinstance(outcome, suite.SuiteResult):
        _print_json(_suite_result_document(outcome))
        return _suite_exit_code(outcome)
    _print_json(
        {
            "state": "skipped" if outcome.skipped else "started",
            "session_name": outcome.session_name,
            "worktree": str(outcome.worktree),
            "phase": outcome.phase_slug,
            "phase_head": outcome.phase_head,
            "log_path": str(outcome.log_path),
            "exit_path": str(outcome.exit_path),
            "skip_reason": outcome.skip_reason,
            "policy": _policy_document(outcome.policy) if outcome.policy else None,
        }
    )
    return 0


def _cmd_suite_poll(args: argparse.Namespace) -> int:
    try:
        job = _suite_job(args)
        result = suite.poll_suite(job, allow_dirty=args.allow_dirty)
    except (OSError, RuntimeError, StoreBindingError, ValueError) as exc:
        print(f"orchestra suite poll: {exc}", file=sys.stderr)
        return 2
    if result is None:
        _print_json(
            {
                "state": "running",
                "session_name": job.session_name,
                "phase": job.phase_slug,
                "phase_head": job.phase_head,
                "log_path": str(job.log_path),
                "exit_path": str(job.exit_path),
            }
        )
        return 3
    _print_json(_suite_result_document(result))
    return _suite_exit_code(result)


def _cmd_suite_collect(args: argparse.Namespace) -> int:
    try:
        result = suite.collect_suite(_suite_job(args), allow_dirty=args.allow_dirty)
    except (OSError, RuntimeError, StoreBindingError, ValueError) as exc:
        print(f"orchestra suite collect: {exc}", file=sys.stderr)
        return 2
    _print_json(_suite_result_document(result))
    return _suite_exit_code(result)


def _cmd_suite_record(args: argparse.Namespace) -> int:
    work = _cwd(args)
    try:
        job = _suite_job(args)
        result = suite.poll_suite(job, allow_dirty=args.allow_dirty)
        if result is None:
            print(
                "orchestra suite record: suite is still running; "
                "poll it until it finishes",
                file=sys.stderr,
            )
            return 3
        record = suite.record_suite_check_run(
            store_root=_store_root(args, work),
            phase_slug=args.phase,
            effort=args.effort,
            suite=result,
            criterion_id=args.criterion_id,
        )
    except (OSError, RuntimeError, StoreBindingError, ValueError) as exc:
        print(f"orchestra suite record: {exc}", file=sys.stderr)
        return 2
    _print_json({"ok": True, "op": "suite-record", "record": record})
    return 0


def _cmd_store_path(args: argparse.Namespace) -> int:
    try:
        target = resolve_store(_cwd(args))
    except (OSError, StoreBindingError) as exc:
        print(f"orchestra store path: {exc}", file=sys.stderr)
        return 2
    if target.store is None:
        print(
            f"orchestra store path: no artifact store under {target.root}",
            file=sys.stderr,
        )
        return 2
    if args.json:
        _print_json(
            {
                "root": str(target.root),
                "store": str(target.store),
                "contract": str(target.contract) if target.contract else None,
                "binding": target.binding.store if target.binding else None,
            }
        )
    else:
        print(target.store)
    return 0


def _cmd_store_run(args: argparse.Namespace) -> int:
    argv = list(args.args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("orchestra store run: needs adaptive-artifacts arguments", file=sys.stderr)
        return 2
    try:
        result = aa.run_aa(*argv, root=aa.find_store_root(_cwd(args)))
    except (OSError, RuntimeError, StoreBindingError) as exc:
        print(f"orchestra store run: {exc}", file=sys.stderr)
        return 2
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    return result.returncode


def _cmd_store_ensure(args: argparse.Namespace) -> int:
    root = project_root(_cwd(args))
    artifacts = root / ".artifacts"
    design = artifacts / "project-design.json"
    try:
        artifacts.mkdir(parents=True, exist_ok=True)
        if not design.is_file():
            design.write_text(contract_path().read_text(encoding="utf-8"), encoding="utf-8")
        target = resolve_store(root)
    except (OSError, RuntimeError, StoreBindingError, ValueError) as exc:
        print(f"orchestra store ensure: {exc}", file=sys.stderr)
        return 2
    payload = {
        "root": str(root),
        "artifacts": str(artifacts),
        "design": str(design),
        "store": str(target.store) if target.store else None,
        "store_ready": bool(target.store and (target.store / "meta.json").is_file()),
    }
    if args.json:
        _print_json(payload)
    else:
        print(payload["store"] or payload["artifacts"])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        outcome = run_check(
            acceptance_id=args.acceptance,
            cwd=work,
            allow_dirty=args.allow_dirty,
            execution_report=args.execution_report,
            timeout=args.timeout,
        )
        if outcome.record is not None:
            print(json.dumps({"ok": True, "op": "check", "record": outcome.record}, indent=2))
        if outcome.message:
            print(outcome.message, file=sys.stderr)
        return outcome.exit_code
    if args.command == "close-batch":
        # Lazy: close-batch is the only command that may need the affidavit
        # checkout, so an installed CLI without one still starts.
        from orchestra.close_batch import main as close_batch_main

        argv = ["--input", args.input, "--out", args.out]
        if args.cwd is not None:
            argv.extend(["--cwd", args.cwd])
        return close_batch_main(argv)
    if args.command == "install":
        from orchestra.install import main as install_main

        return install_main(args)
    if args.command == "contract":
        try:
            path = contract_path()
            text = path.read_text(encoding="utf-8")
            json.loads(text)
            if args.write is not None:
                destination = Path(args.write).expanduser()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(text, encoding="utf-8")
                print(destination)
                return 0
        except (OSError, ValueError) as exc:
            print(f"orchestra contract: {exc}", file=sys.stderr)
            return 1
        if args.path:
            print(path)
            return 0
        print(text, end="" if text.endswith("\n") else "\n")
        return 0
    if args.command == "project-field":
        try:
            outcome = rewrite_project_field(args.design)
        except (OSError, ValueError) as exc:
            print(f"orchestra project-field: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps({"op": "project-field", "path": args.design, "outcome": outcome}))
        else:
            print(outcome)
        return 1 if outcome == STOPPED else 0
    if args.command == "sessions":
        try:
            if args.action == "report":
                return report_sessions(args.root, records=args.records)
            return aggregate_sessions(args.report)
        except (OSError, ModuleNotFoundError) as exc:
            print(f"orchestra sessions: {exc}", file=sys.stderr)
            return 2
    if args.command == "review-brief":
        return _cmd_review_brief(args)
    if args.command == "suite":
        if args.action == "policy":
            return _cmd_suite_policy(args)
        if args.action == "start":
            return _cmd_suite_start(args)
        if args.action == "poll":
            return _cmd_suite_poll(args)
        if args.action == "collect":
            return _cmd_suite_collect(args)
        return _cmd_suite_record(args)
    if args.command == "store":
        if args.action == "path":
            return _cmd_store_path(args)
        if args.action == "run":
            return _cmd_store_run(args)
        return _cmd_store_ensure(args)
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
