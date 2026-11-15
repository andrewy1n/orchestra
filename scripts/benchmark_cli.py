from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import sys
import tempfile
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from orchestra.canon.backend import open_backend
from orchestra.canon.config import new_config
from orchestra.canon.record import base_record
from orchestra.canon.schema import SchemaSet
from orchestra.canon.types import JsonObject, JsonValue, get_list, get_string
from orchestra.tools.cli_tool import CliTool, ProcessHandle
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

ROOT = Path(__file__).resolve().parents[1]
FORMAT = "orchestra-cli-benchmark/1"
FIXTURE_VERSION = "planning-evidence/1"
STAMP = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class Fixture:
    root: Path
    records: int
    task: str
    record_id: str
    fingerprint: str


def build_fixture(root: Path, size: int) -> Fixture:
    if size < 20:
        raise ValueError("fixture size must be at least 20")
    root.mkdir(parents=True, exist_ok=False)
    Git(root, env=clean_environment()).text("init", "-q")
    backend = open_backend(root / ".canon")
    snapshots = {
        name: (ROOT / "orchestra" / name / "schemas" / f"{name}.json").read_text()
        for name in ("score", "conductor", "tuner", "composer")
    }
    versions: dict[str, str] = {}
    for name, text in snapshots.items():
        module: JsonValue = json.loads(text)
        if not isinstance(module, dict) or not isinstance(module.get("version"), str):
            raise ValueError(f"invalid schema: {name}")
        version = module["version"]
        if isinstance(version, str):
            versions[name] = version
    config = new_config(versions)
    config["backend"] = "sqlite"
    backend.init(config, snapshots)
    schemas = SchemaSet.load(backend, config)
    count = 0
    signature = hashlib.sha256(json.dumps(snapshots, sort_keys=True).encode())

    def add(
        record_type: str,
        subject: str,
        payload: JsonObject,
        body: str = "",
        state: str | None = None,
    ) -> str:
        nonlocal count
        count += 1
        record_id = f"rec-00000000-0000-0000-0000-{count:012x}"
        record = base_record(
            schemas.types[record_type],
            subject=subject,
            payload=payload,
            record_id=record_id,
            lifecycle_state=state,
            body=body,
            recorded_at=STAMP,
        )
        signature.update(json.dumps(record, sort_keys=True).encode())
        stored = backend.create_record(record)
        if schemas.types[record_type].lifecycle.appends_only:
            backend.archive_history(stored)
        return record_id

    first_task = ""
    first_id = ""
    with backend.transaction():
        effort = "benchmark-effort"
        add(
            "score:effort",
            effort,
            {"goal": "Measure CLI planning reads", "kind": "deliver", "status": "open"},
        )
        phase_count = max(1, size // 100)
        task_count = (size - 1 - phase_count * 2) // 5
        for phase_index in range(phase_count):
            phase = f"benchmark-phase-{phase_index:03d}"
            requirements: list[JsonValue] = [f"R{i}" for i in range(1, 6)]
            add(
                "score:phase",
                phase,
                {"title": phase, "ordinal": phase_index + 1, "effort": effort},
                "## Problem\n\nMeasure planning reads.\n\n## Approach\n\nUse fixed fixtures.\n\n## Exit criteria\n\nAll criteria pass.\n",
            )
            add(
                "score:specification",
                phase,
                {"weight": "full", "phase": phase, "effort": effort, "requirements": requirements},
                "## Requirements\n\n"
                + "\n".join(f"R{i}: Task {i} produces its result." for i in range(1, 6))
                + "\n\n"
                + "\n\n".join(
                    f"## {heading}\n\nFixed benchmark contract."
                    for heading in (
                        "Acceptance criteria",
                        "Constraints",
                        "Non-goals",
                        "Invariants",
                        "Assumptions",
                    )
                ),
            )
        for task_index in range(task_count):
            phase = f"benchmark-phase-{task_index % phase_count:03d}"
            task = f"benchmark-task-{task_index:04d}"
            requirement = f"R{task_index % 5 + 1}"
            deps: list[JsonValue] = (
                [f"benchmark-task-{task_index - phase_count:04d}"]
                if task_index >= phase_count
                else []
            )
            task_id = add(
                "score:work-item",
                task,
                {
                    "title": task,
                    "phase": phase,
                    "effort": effort,
                    "kind": "deliver",
                    "assignee": "",
                    "requirements": [requirement],
                    "depends_on": deps,
                },
                "## Description\n\nProduce the fixed benchmark result.\n\n## Approach\n\nRun the acceptance check.\n",
                "done" if task_index % 3 else "planned",
            )
            if not first_task:
                first_task, first_id = task, task_id
            acceptance = add(
                "score:acceptance",
                task,
                {
                    "method": "check",
                    "phase": phase,
                    "effort": effort,
                    "verify_command": "true",
                    "requirement": requirement,
                },
            )
            for run in range(3):
                add(
                    "tuner:check-run",
                    f"{task}-run-{run}",
                    {
                        "criterion_id": acceptance,
                        "revision": "benchmark-revision",
                        "result": "fail" if run == 0 else "pass",
                        "effort": effort,
                        "method": "check",
                        "signed_by": "",
                        "requirement": requirement,
                        "evidence_kind": "unit",
                    },
                )
        while count < size:
            add(
                "tuner:check-run",
                f"benchmark-extra-{count}",
                {
                    "criterion_id": "benchmark-history",
                    "revision": "benchmark-revision",
                    "result": "pass",
                    "effort": effort,
                    "method": "check",
                    "signed_by": "",
                },
            )
    return Fixture(root, count, first_task, first_id, signature.hexdigest())


def clean_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("CANON_", "ORCHESTRA_", "GIT_"))
    }


def command_environment(fixture: Fixture) -> dict[str, str]:
    env = clean_environment()
    env.update(
        {
            "PYTHONPATH": str(ROOT),
            "PYTHONHASHSEED": "0",
            "CANON_STORE": str(fixture.root / ".canon"),
            "ORCHESTRA_STORE": str(fixture.root / ".canon"),
            "CANON_READONLY": "1",
        }
    )
    return env


@dataclass(frozen=True)
class Case:
    name: str
    argv: tuple[str, ...]
    check: str


def cases(fixture: Fixture) -> list[Case]:
    return [
        Case("orchestra-help", ("orchestra.cli", "--help"), "orchestra-help"),
        Case("canon-help", ("orchestra.canon", "--help"), "canon-help"),
        Case("canon-get", ("orchestra.canon", "get", "--id", fixture.record_id), "get"),
        Case("canon-list", ("orchestra.canon", "list", "--full"), "list"),
        Case(
            "canon-list-filtered",
            (
                "orchestra.canon",
                "list",
                "--type",
                "score:work-item",
                "--subject",
                fixture.task,
                "--exact-subject",
            ),
            "filtered",
        ),
        Case("canon-validate", ("orchestra.canon", "validate"), "validate"),
        Case("handoff", ("orchestra.cli", "handoff"), "# Project Handoff"),
        Case("plan", ("orchestra.cli", "view", "plan"), "# Project Plan"),
        Case("status", ("orchestra.cli", "view", "status"), "# Project Status"),
        Case("verification", ("orchestra.cli", "view", "verification"), "# Project Verification"),
        Case("brief", ("orchestra.cli", "brief", fixture.task), f"# Brief: {fixture.task}"),
    ]


def validate_output(case: Case, stdout: str, fixture: Fixture) -> str | None:
    if case.check.endswith("-help"):
        expected = "usage: orchestra" if case.check == "orchestra-help" else "usage: canon"
        return None if expected in stdout else f"missing help usage: {expected}"
    if case.check in ("get", "list", "filtered", "validate"):
        try:
            value: JsonValue = json.loads(stdout)
        except ValueError:
            return "output is not valid JSON"
        if not isinstance(value, dict):
            return "output is not a JSON object"
        if case.check == "validate":
            return (
                None
                if value.get("status") == "valid"
                and value.get("errors") == []
                and value.get("records") == fixture.records
                else "validation did not report a valid store with the expected record count"
            )
        if case.check == "get":
            return (
                None
                if value.get("id") == fixture.record_id and value.get("subject") == fixture.task
                else "lookup returned the wrong record"
            )
        records = get_list(value, "records")
        expected_count = fixture.records if case.check == "list" else 1
        if (
            records is None
            or len(records) != expected_count
            or value.get("count") != expected_count
        ):
            return f"list did not return {expected_count} records"
        if case.check == "filtered" and (
            not isinstance(records[0], dict) or records[0].get("subject") != fixture.task
        ):
            return "filtered list returned the wrong task"
        return None
    markers = (
        (case.check, "Measure CLI planning reads")
        if case.name == "handoff"
        else (case.check, "benchmark-phase-000", fixture.task, "R1")
    )
    for marker in markers:
        if marker not in stdout:
            return f"missing view content: {marker}"
    return None


def stop_group(process: ProcessHandle) -> None:
    process.terminate_group()
    with suppress(ToolError):
        process.wait(timeout=0.2)
    if process.group_exists:
        process.kill_group()
    process.wait(timeout=5)


def execute(argv: Sequence[str], cwd: Path, env: dict[str, str], timeout: float) -> JsonObject:
    runner = CliTool(cwd)
    start = perf_counter()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = runner.start_process(argv, env=env, stdout=stdout, stderr=stderr)
        timed_out = False
        try:
            code = process.wait(timeout=timeout)
        except ToolError:
            timed_out = True
            stop_group(process)
            code = process.returncode
        except BaseException:
            stop_group(process)
            raise
        else:
            if process.group_exists:
                stop_group(process)
        elapsed = perf_counter() - start
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read()
        err = stderr.read()
    return {
        "seconds": elapsed,
        "exit_code": code,
        "timed_out": timed_out,
        "stdout": out.decode("utf-8", errors="replace"),
        "stderr": err.decode("utf-8", errors="replace"),
        "stdout_bytes": len(out),
        "stderr_bytes": len(err),
    }


def measure(case: Case, fixture: Fixture, repeat: int, timeout: float) -> JsonObject:
    samples: list[JsonValue] = []
    durations: list[float] = []
    error: str | None = None
    for _ in range(repeat):
        try:
            sample = execute(
                (sys.executable, "-m", *case.argv),
                fixture.root,
                command_environment(fixture),
                timeout,
            )
        except ToolError as exc:
            error = str(exc)
            break
        stdout = get_string(sample, "stdout") or ""
        if sample.get("timed_out"):
            error = f"timeout after {timeout:g} seconds"
        elif sample.get("exit_code") != 0:
            error = f"exit code {sample.get('exit_code')}"
        else:
            error = validate_output(case, stdout, fixture)
        if error:
            sample["error"] = error
            sample["stdout_excerpt"] = stdout[-2000:]
            sample["stderr_excerpt"] = (get_string(sample, "stderr") or "")[-2000:]
        del sample["stdout"], sample["stderr"]
        samples.append(sample)
        seconds = sample.get("seconds")
        if isinstance(seconds, (int, float)) and not error:
            durations.append(seconds)
        if error:
            break
    return {
        "case": case.name,
        "argv": ["python", "-m", *case.argv],
        "records": fixture.records,
        "fixture": fixture.fingerprint,
        "status": "fail" if error else "pass",
        "error": error,
        "samples": samples,
        "median_seconds": statistics.median(durations) if durations else None,
        "min_seconds": min(durations) if durations else None,
        "max_seconds": max(durations) if durations else None,
    }


def run_benchmarks(
    sizes: Sequence[int], repeat: int, timeout: float, selected: Sequence[str], output: Path
) -> int:
    if repeat < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("repeat and timeout must be positive")
    results: list[JsonValue] = []
    report: JsonObject = {
        "format": FORMAT,
        "fixture_version": FIXTURE_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "revision": Git(ROOT, env=clean_environment()).head(),
        "dirty": bool(Git(ROOT, env=clean_environment()).status_porcelain()),
        "environment": {
            "python": platform.python_version(),
            "executable": sys.executable,
            "checkout": str(ROOT),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "load_average": list(os.getloadavg()),
        },
        "repeat": repeat,
        "timeout_seconds": timeout,
        "results": results,
    }
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="orchestra-cli-benchmark-") as directory:
        for size in sizes:
            fixture = build_fixture(Path(directory) / f"store-{size}", size)
            available = cases(fixture)
            unknown = set(selected) - {case.name for case in available}
            if unknown:
                raise ValueError(f"unknown cases: {', '.join(sorted(unknown))}")
            for case in available:
                if selected and case.name not in selected:
                    continue
                result = measure(case, fixture, repeat, timeout)
                results.append(result)
                output.write_text(json.dumps(report, indent=2) + "\n")
                median = result.get("median_seconds")
                timing = (
                    f"{median:.3f}s"
                    if isinstance(median, (int, float))
                    else str(result.get("error"))
                )
                print(f"{size:6d}  {case.name:22s} {result['status']}: {timing}", flush=True)
    return int(
        any(isinstance(result, dict) and result.get("status") != "pass" for result in results)
    )


def read_report(path: Path) -> JsonObject:
    value: JsonValue = json.loads(path.read_text())
    if (
        not isinstance(value, dict)
        or value.get("format") != FORMAT
        or not isinstance(value.get("results"), list)
    ):
        raise ValueError(f"invalid benchmark report: {path}")
    return value


def compare(before: JsonObject, after: JsonObject) -> list[str]:
    for key in ("format", "fixture_version", "timeout_seconds"):
        if before.get(key) != after.get(key):
            raise ValueError(f"incompatible reports: {key}")

    def rows(report: JsonObject) -> dict[tuple[int, str], JsonObject]:
        result: dict[tuple[int, str], JsonObject] = {}
        for row in get_list(report, "results") or []:
            if not isinstance(row, dict):
                raise ValueError("invalid result row")
            size, name = row.get("records"), row.get("case")
            if not isinstance(size, int) or not isinstance(name, str) or (size, name) in result:
                raise ValueError("invalid or duplicate case")
            result[size, name] = row
        return result

    old, new = rows(before), rows(after)
    if old.keys() != new.keys() or not old:
        raise ValueError("incompatible reports: case sets differ or are empty")
    lines = ["records  case                    before       after       change"]
    for key, previous in old.items():
        current = new[key]
        if previous.get("fixture") != current.get("fixture") or previous.get("argv") != current.get(
            "argv"
        ):
            raise ValueError(f"incompatible fixture or command: {key}")
        a, b = previous.get("median_seconds"), current.get("median_seconds")
        if (
            previous.get("status") == current.get("status") == "pass"
            and isinstance(a, (int, float))
            and isinstance(b, (int, float))
            and a > 0
        ):
            lines.append(
                f"{key[0]:7d}  {key[1]:22s} {a:9.3f}s  {b:9.3f}s  {(b / a - 1) * 100:+7.1f}%"
            )
        else:
            lines.append(
                f"{key[0]:7d}  {key[1]:22s} {previous.get('status')} -> {current.get('status')} (no timing comparison)"
            )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure CLI processes against fixed temporary stores."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--sizes", nargs="+", type=int, default=[100, 1000, 6000])
    run.add_argument("--repeat", type=int, default=3)
    run.add_argument("--timeout", type=float, default=10)
    run.add_argument("--cases", nargs="+", default=[])
    comparison = sub.add_parser("compare")
    comparison.add_argument("before", type=Path)
    comparison.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            print("\n".join(compare(read_report(args.before), read_report(args.after))))
            return 0
        if len(set(args.sizes)) != len(args.sizes) or any(size < 20 for size in args.sizes):
            raise ValueError("sizes must be unique integers of at least 20")
        return run_benchmarks(args.sizes, args.repeat, args.timeout, args.cases, args.output)
    except (OSError, ToolError, ValueError) as exc:
        print(f"benchmark: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
