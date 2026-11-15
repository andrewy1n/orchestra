from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

from orchestra.canon.project import open_store
from orchestra.canon.types import JsonObject
from orchestra.tools.git import Git
from scripts import benchmark_cli as benchmark


def test_fixture_has_fixed_data_and_valid_event_history(tmp_path: Path) -> None:
    first = benchmark.build_fixture(tmp_path / "first", 100)
    second = benchmark.build_fixture(tmp_path / "second", 100)
    project = open_store(first.root, read_only=True)
    assert len(project.records()) == 100
    assert project.validate() == []
    assert first.fingerprint == second.fingerprint
    assert project.get(first.record_id)["subject"] == first.task
    assert {record["record_type"] for record in project.records()} >= {
        "score:phase",
        "score:specification",
        "score:work-item",
        "score:acceptance",
        "tuner:check-run",
    }


def test_real_runner_ignores_parent_store_and_git_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = tmp_path / "sentinel"
    sentinel.mkdir()
    marker = sentinel / "untouched"
    marker.write_text("keep")
    monkeypatch.setenv("CANON_STORE", str(sentinel))
    monkeypatch.setenv("ORCHESTRA_STORE", str(sentinel))
    monkeypatch.setenv("CANON_SCHEMA_PATH", str(sentinel))
    monkeypatch.setenv("GIT_DIR", str(sentinel / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(sentinel))
    monkeypatch.setenv("GIT_INDEX_FILE", str(sentinel / "index"))
    output = tmp_path / "report.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(benchmark.ROOT)
    result = benchmark.execute(
        (
            sys.executable,
            "-m",
            "scripts.benchmark_cli",
            "run",
            "--sizes",
            "100",
            "--repeat",
            "2",
            "--timeout",
            "10",
            "--output",
            str(output),
        ),
        benchmark.ROOT,
        env,
        30,
    )
    assert result["exit_code"] == 0, result
    report = benchmark.read_report(output)
    rows = report["results"]
    assert isinstance(rows, list)
    assert len(rows) == 11
    for row in rows:
        assert isinstance(row, dict)
        assert row["status"] == "pass", row
        samples = row["samples"]
        assert isinstance(samples, list) and len(samples) == 2
        assert isinstance(row["median_seconds"], float)
        for sample in samples:
            assert isinstance(sample, dict)
            size = sample["stdout_bytes"]
            assert isinstance(size, int) and size > 0
    assert list(sentinel.iterdir()) == [marker]
    assert benchmark.compare(report, report)


def test_output_validation_rejects_empty_wrong_and_incomplete_results(tmp_path: Path) -> None:
    fixture = benchmark.build_fixture(tmp_path / "store", 20)
    for case in benchmark.cases(fixture):
        assert benchmark.validate_output(case, "", fixture) is not None
    lookup = next(case for case in benchmark.cases(fixture) if case.name == "canon-get")
    assert benchmark.validate_output(
        lookup, json.dumps({"id": fixture.record_id, "subject": "wrong"}), fixture
    )
    status = next(case for case in benchmark.cases(fixture) if case.name == "status")
    assert benchmark.validate_output(status, "# Project Status\nbenchmark-effort", fixture)
    validation = next(case for case in benchmark.cases(fixture) if case.name == "canon-validate")
    assert benchmark.validate_output(validation, '{"status":"valid","errors":["broken"]}', fixture)
    assert benchmark.validate_output(
        validation, '{"status":"valid","errors":[],"records":0}', fixture
    )


def test_failed_case_writes_report_and_stops_repetitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = benchmark.Case("bad-output", ("orchestra.cli", "--help"), "# Required result")

    def selected_cases(fixture: benchmark.Fixture) -> list[benchmark.Case]:
        return [bad]

    monkeypatch.setattr(benchmark, "cases", selected_cases)
    output = tmp_path / "failed.json"
    assert benchmark.run_benchmarks([20], 3, 5, [], output) == 1
    report = benchmark.read_report(output)
    rows = report["results"]
    assert isinstance(rows, list) and len(rows) == 1
    row = rows[0]
    assert isinstance(row, dict) and row["status"] == "fail"
    samples = row["samples"]
    assert isinstance(samples, list) and len(samples) == 1
    assert row["median_seconds"] is None
    assert isinstance(samples[0], dict) and "stdout_excerpt" in samples[0]


def test_command_failure_preserves_exit_code_and_stderr(tmp_path: Path) -> None:
    result = benchmark.execute(
        (sys.executable, "-c", "import sys; print('failure', file=sys.stderr); sys.exit(7)"),
        tmp_path,
        dict(os.environ),
        5,
    )
    assert result["exit_code"] == 7
    assert result["timed_out"] is False
    assert result["stderr"] == "failure\n"


def _running(pid: int) -> bool:
    path = Path(f"/proc/{pid}/stat")
    return path.exists() and path.read_text().split()[2] not in ("Z", "X")


@pytest.mark.skipif(sys.platform != "linux", reason="process state check uses procfs")
def test_timeout_stops_parent_and_term_ignoring_child(tmp_path: Path) -> None:
    pid_file = tmp_path / "child.pid"
    code = """import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
pid = os.fork()
if pid == 0:
    with open(sys.argv[1], 'w') as stream:
        stream.write(str(os.getpid()))
while True:
    time.sleep(1)
"""
    result = benchmark.execute(
        (sys.executable, "-c", code, str(pid_file)), tmp_path, dict(os.environ), 0.5
    )
    assert result["timed_out"] is True
    pid = int(pid_file.read_text())
    deadline = time.monotonic() + 2
    while _running(pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not _running(pid)


def _report(seconds: float = 1) -> JsonObject:
    return {
        "format": benchmark.FORMAT,
        "fixture_version": benchmark.FIXTURE_VERSION,
        "timeout_seconds": 10,
        "results": [
            {
                "records": 100,
                "case": "status",
                "fixture": "fixed",
                "argv": ["python", "-m", "orchestra.cli", "view", "status"],
                "status": "pass",
                "median_seconds": seconds,
            }
        ],
    }


def test_comparison_reports_slowdown_without_failure() -> None:
    assert "+100.0%" in benchmark.compare(_report(), _report(2))[1]


@pytest.mark.parametrize(
    "key,value", [("fixture_version", "different"), ("timeout_seconds", 30), ("results", [])]
)
def test_comparison_refuses_incompatible_reports(key: str, value: object) -> None:
    report = _report()
    if isinstance(value, (str, int, list)):
        report[key] = value
    with pytest.raises(ValueError, match="incompatible"):
        benchmark.compare(_report(), report)


def test_comparison_refuses_changed_fixture() -> None:
    report = _report()
    rows = report["results"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    rows[0]["fixture"] = "different"
    with pytest.raises(ValueError, match="fixture"):
        benchmark.compare(_report(), report)


def test_invalid_arguments_fail_before_running(tmp_path: Path) -> None:
    assert benchmark.main(["run", "--output", str(tmp_path / "x"), "--sizes", "1"]) == 2
    assert benchmark.main(["run", "--output", str(tmp_path / "x"), "--repeat", "0"]) == 2
    assert benchmark.main(["run", "--output", str(tmp_path / "x"), "--timeout", "nan"]) == 2


def test_fixture_git_repository_is_local(tmp_path: Path) -> None:
    fixture = benchmark.build_fixture(tmp_path / "store", 20)
    assert Git(fixture.root).root() == fixture.root


def test_timeout_writes_failure_report(tmp_path: Path) -> None:
    output = tmp_path / "timeout.json"
    assert benchmark.run_benchmarks([20], 3, 0.000001, ["orchestra-help"], output) == 1
    rows = benchmark.read_report(output)["results"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    row = rows[0]
    assert row["status"] == "fail"
    assert row["median_seconds"] is None
    samples = row["samples"]
    assert isinstance(samples, list) and len(samples) == 1
    assert isinstance(samples[0], dict) and samples[0]["timed_out"] is True


def test_comparison_does_not_treat_failed_samples_as_timings() -> None:
    report = _report()
    rows = report["results"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    rows[0]["status"] = "fail"
    assert "pass -> fail (no timing comparison)" in benchmark.compare(_report(), report)[1]
