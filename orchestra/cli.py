"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from orchestra import reviewer, view_cli

try:
    from orchestra.canon.project import StoreBindingError, open_store
    from orchestra.canon.store import StoreError
except ModuleNotFoundError:
    StoreBindingError = None
    open_store = None
    StoreError = None

try:
    from orchestra import suite
except ModuleNotFoundError:
    suite = None

try:
    from orchestra.check import DEFAULT_TIMEOUT_S, git_head, run_check
except ModuleNotFoundError:
    DEFAULT_TIMEOUT_S = 600.0
    git_head = None
    run_check = None

from orchestra.sessions import aggregate as aggregate_sessions
from orchestra.sessions import report as report_sessions


STORE_SCHEMAS = ("score", "conductor", "tuner")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestra",
        description=(
            "orchestra CLI: checks, reviewer briefs, phase suite, "
            "and store access through the artifact library."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    view_cli.add_parsers(sub)
    sub.add_parser(
        "verify",
        add_help=False,
        help="Verdict, attestation, claims, audit, and evidence binding",
    )

    check = sub.add_parser(
        "check",
        help="Run an acceptance verify_command and write an tuner:check-run",
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
        help="Phase suite: configured policy, background run, collect, record",
    )
    suite_sub = suite_parser.add_subparsers(dest="action", required=True)

    suite_policy = suite_sub.add_parser(
        "policy",
        help="Print the configured phase_gate.suite policy as JSON",
    )
    suite_policy.add_argument("--cwd", default=None, help="Worktree (default: cwd)")

    suite_start = suite_sub.add_parser(
        "start",
        help="Start the configured suite in a detached tmux session",
    )
    _add_suite_job_arguments(suite_start)
    suite_start.add_argument(
        "--command",
        dest="suite_command",
        default=None,
        help="Override the configured suite command",
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
        help="Collect a finished suite and write its tuner:check-run",
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
        help="Open the bound store and read or write it through the library",
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
        help="Print the resolved root, store, and binding as JSON",
    )
    store_run = store_sub.add_parser(
        "run",
        help="Run a library read or write against the opened store",
    )
    store_run.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="library arguments, after '--'",
    )
    store_ensure = store_sub.add_parser(
        "ensure",
        help="Create the store with the plan, run, and aff schemas when absent",
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


def _git_root(directory: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return directory.resolve()


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
    work: Path,
) -> tuple[list[dict[str, object]], list[str]]:
    """Read the reviewer-allowed kinds from the opened store."""
    project = open_store(work)
    records: list[dict[str, object]] = []
    failures: list[str] = []
    for kind in sorted(reviewer.ALLOWED_KINDS):
        record_type = f"score:{kind}"
        try:
            rows = project.list(record_type)
        except StoreError as exc:
            failures.append(f"{record_type}: {exc}")
            continue
        records.extend(row for row in rows if isinstance(row, dict))
    if not records and failures:
        raise RuntimeError("; ".join(failures))
    return records, failures


def _cmd_review_brief(args: argparse.Namespace) -> int:
    work = _cwd(args)
    try:
        records, failures = _load_review_records(work)
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
        directory = Path(args.store).expanduser() if getattr(args, "store", None) else work
        record = suite.record_suite_check_run(
            store_root=directory,
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


def _flag_values(argv: list[str]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    index = 0
    while index < len(argv):
        item = argv[index]
        if item.startswith("--") and index + 1 < len(argv) and not argv[index + 1].startswith("--"):
            values.setdefault(item, []).append(argv[index + 1])
            index += 2
        else:
            index += 1
    return values


def _dispatch_store(project, argv: list[str]) -> tuple[object, int]:
    verb = argv[0]
    flags = _flag_values(argv[1:])
    if verb == "list":
        record_type = (flags.get("--type") or [None])[0]
        if not record_type:
            raise ValueError("list requires --type")
        rows = project.list(record_type)
        state = (flags.get("--state") or [None])[0]
        if state:
            rows = [row for row in rows if row.get("lifecycle_state") == state]
        return {"records": rows, "count": len(rows)}, 0
    if verb == "get":
        record_id = (flags.get("--id") or [None])[0]
        if not record_id:
            raise ValueError("get requires --id")
        record_type = (flags.get("--type") or [None])[0]
        return project.get(record_id, record_type), 0
    if verb == "create":
        record_type = (flags.get("--type") or [None])[0]
        subject = (flags.get("--subject") or [None])[0]
        payload_text = (flags.get("--payload") or ["{}"])[0]
        body = (flags.get("--body") or [None])[0]
        if not record_type or not subject:
            raise ValueError("create requires --type and --subject")
        record = project.create(
            record_type=record_type,
            subject=subject,
            payload=json.loads(payload_text),
            body=body,
        )
        return {"ok": True, "op": "create", "record": record}, 0
    if verb == "apply":
        source = (flags.get("--file") or [None])[0]
        raw = Path(source).read_text(encoding="utf-8") if source else sys.stdin.read()
        operations = [json.loads(line) for line in raw.splitlines() if line.strip()]
        return project.apply(operations), 0
    raise ValueError(f"unsupported store operation {verb!r}")


def _cmd_store_path(args: argparse.Namespace) -> int:
    try:
        project = open_store(_cwd(args))
    except (OSError, StoreBindingError) as exc:
        print(f"orchestra store path: {exc}", file=sys.stderr)
        return 2
    if args.json:
        _print_json(
            {
                "root": str(project.project_root),
                "store": str(project.store_path),
                "binding": project.binding.location,
            }
        )
    else:
        print(project.store_path)
    return 0


def _cmd_store_run(args: argparse.Namespace) -> int:
    argv = list(args.args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("orchestra store run: needs library arguments", file=sys.stderr)
        return 2
    try:
        project = open_store(_cwd(args))
        payload, code = _dispatch_store(project, argv)
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        print(f"orchestra store run: {exc}", file=sys.stderr)
        return 2
    text = payload if isinstance(payload, str) else json.dumps(payload)
    print(text, end="" if text.endswith("\n") else "\n")
    return code


def _cmd_store_ensure(args: argparse.Namespace) -> int:
    from orchestra.canon.store import Store
    from orchestra.canon.sync import init_store

    root = _git_root(_cwd(args))
    artifacts = root / ".canon"
    try:
        project = open_store(root)
    except StoreBindingError:
        project = None
    except OSError as exc:
        print(f"orchestra store ensure: {exc}", file=sys.stderr)
        return 2
    if project is None:
        try:
            artifacts.mkdir(parents=True, exist_ok=True)
            init_store(Store(artifacts), list(STORE_SCHEMAS))
            project = open_store(root)
        except (OSError, StoreError, StoreBindingError) as exc:
            print(f"orchestra store ensure: {exc}", file=sys.stderr)
            return 2
    payload = {
        "root": str(root),
        "artifacts": str(artifacts),
        "store": str(project.store_path),
        "store_ready": (project.store_path / "config.json").is_file(),
    }
    if args.json:
        _print_json(payload)
    else:
        print(payload["store"])
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["verify"]:
        from orchestra.tuner.cli import main as verify_main

        return verify_main(argv[1:])
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
        from orchestra.close_batch import main as close_batch_main

        argv = ["--input", args.input, "--out", args.out]
        if args.cwd is not None:
            argv.extend(["--cwd", args.cwd])
        return close_batch_main(argv)
    if args.command == "install":
        from orchestra.install import main as install_main

        return install_main(args)
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
    if args.command in view_cli.COMMANDS:
        return view_cli.run(args)
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
