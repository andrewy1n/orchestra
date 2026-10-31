"""The CLI exposes the reviewer, suite, and store surface skills call by name.

A skill must be able to run the phase-end reviewer, the configured suite, and
store-bound ``canon`` calls with ``orchestra`` alone. These tests
pin the subcommands the skills name and smoke-call each one without touching a
real store or tmux server.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

sys.path.insert(0, str(REPO_ROOT))

from orchestra import cli
from orchestra.conductor import suite

# Every runtime call a skill makes must be one of these named commands.
HELP_PATHS = [
    ["idea"],
    ["analyze"],
    ["review-brief"],
    ["suite", "policy"],
    ["suite", "start"],
    ["suite", "poll"],
    ["suite", "collect"],
    ["suite", "record"],
    ["store", "path"],
    ["store", "run"],
    ["store", "ensure"],
]


def run(argv: list[str], capsys) -> tuple[int, str, str]:
    code = cli.main(argv)
    out, err = capsys.readouterr()
    return code, out, err


def completed(args: tuple[str, ...], stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(list(args), returncode, stdout, "")


def make_design(path: Path, suite_policy: dict | None = None) -> Path:
    config = path / ".canon" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    settings: dict = {}
    if suite_policy is not None:
        settings["conductor"] = {"phase_gate": {"suite": suite_policy}}
    config.write_text(json.dumps({"format": "canon/1", "schemas": {}, "settings": settings}))
    return config


def finished_suite(work: Path, phase: str = "p1", exit_code: str = "0") -> None:
    directory = work / ".suite"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"orchestra-suite-{phase}.log").write_text("1 passed in 0.01s\n")
    (directory / f"orchestra-suite-{phase}.exit").write_text(f"{exit_code}\n")


@pytest.mark.parametrize("argv", HELP_PATHS, ids=lambda argv: "-".join(argv))
def test_each_runtime_command_has_help(argv):
    with pytest.raises(SystemExit) as exit_info:
        cli.main([*argv, "--help"])
    assert exit_info.value.code == 0


def test_top_level_help_names_the_runtime_surface(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--help"])
    assert exit_info.value.code == 0
    text = capsys.readouterr().out
    for name in ("analyze", "review-brief", "suite", "store"):
        assert name in text


def test_review_brief_smoke(tmp_path, monkeypatch, capsys):
    records = [
        {
            "record_type": "score:work-item",
            "subject": "tabs",
            "title": "Implement tabs",
            "body": "Implement the status tabs.",
        },
        {
            "record_type": "score:acceptance",
            "subject": "tabs",
            "criterion": "Tabs render both filters.",
        },
        {
            "record_type": "score:requirement",
            "subject": "R6",
            "title": "R6",
            "body": "Name commands, not modules.",
        },
        {
            "record_type": "conductor:execution-report",
            "subject": "tabs",
            "body": "SECRET_BUILDER_NOTES",
        },
    ]
    calls: list[str] = []

    class _Project:
        def list(self, record_type: str):
            calls.append(record_type)
            return [row for row in records if row.get("record_type") == record_type]

    monkeypatch.setattr(cli, "open_store", lambda directory: _Project())
    monkeypatch.setattr(
        "orchestra.conductor.reviewer.git_phase_diff", lambda *a, **k: "+reviewed line"
    )

    code, out, err = run(
        [
            "review-brief",
            "--cwd",
            str(tmp_path),
            "--base",
            "main",
            "--phase-head",
            "abc1234",
        ],
        capsys,
    )
    assert code == 0, err
    assert "Implement the status tabs." in out
    assert "Tabs render both filters." in out
    assert "Name commands, not modules." in out
    assert "+reviewed line" in out
    assert "main..abc1234" in out
    assert "SECRET_BUILDER_NOTES" not in out
    assert calls


def test_suite_policy_smoke(tmp_path, capsys):
    make_design(
        tmp_path,
        {"mode": "smoke", "command": "pytest -q", "gate": "required"},
    )
    code, out, err = run(["suite", "policy", "--cwd", str(tmp_path)], capsys)
    assert code == 0, err
    policy = json.loads(out)
    assert policy["mode"] == "smoke"
    assert policy["gate"] == "required"
    assert policy["run_locally"] is True
    assert policy["blocks_merge"] is True


def test_suite_start_smoke(tmp_path, monkeypatch, capsys):
    work = tmp_path / "worktree"
    work.mkdir()
    started = suite.SuiteStart(
        session_name="orchestra-suite-p1",
        worktree=work,
        phase_slug="p1",
        phase_head="abc1234",
        log_path=work / ".suite" / "orchestra-suite-p1.log",
        exit_path=work / ".suite" / "orchestra-suite-p1.exit",
        started_monotonic=time.monotonic(),
    )
    monkeypatch.setattr(
        "orchestra.conductor.suite.start_suite_background", lambda **kwargs: started
    )
    code, out, err = run(["suite", "start", "--cwd", str(work), "--phase", "p1"], capsys)
    assert code == 0, err
    handle = json.loads(out)
    assert handle["state"] == "started"
    assert handle["session_name"] == "orchestra-suite-p1"
    assert handle["exit_path"].endswith("orchestra-suite-p1.exit")


def _git_worktree() -> Path:
    repo = make_git_repo()
    (repo / ".gitignore").write_text(".suite/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "ignore suite output")
    return repo


def test_suite_poll_running_then_finished(capsys):
    repo = _git_worktree()
    code, out, err = run(["suite", "poll", "--cwd", str(repo), "--phase", "p1"], capsys)
    assert code == 3
    assert json.loads(out)["state"] == "running"

    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    finished_suite(repo)
    code, out, err = run(["suite", "poll", "--cwd", str(repo), "--phase", "p1"], capsys)
    assert code == 0, err
    result = json.loads(out)
    assert result["result"] == "pass"
    assert result["revision"] == head
    assert result["exit_code"] == 0


def test_suite_collect_reports_failures(capsys):
    repo = _git_worktree()
    finished_suite(repo, exit_code="1")
    (repo / ".suite" / "orchestra-suite-p1.log").write_text(
        "FAILED tests/test_foo.py::test_bar - AssertionError\n"
    )
    code, out, _ = run(["suite", "collect", "--cwd", str(repo), "--phase", "p1"], capsys)
    assert code == 1
    result = json.loads(out)
    assert result["result"] == "fail"
    assert result["failing_node_ids"] == ["tests/test_foo.py::test_bar"]


def test_suite_record_smoke(tmp_path, monkeypatch, capsys):
    repo = _git_worktree()
    finished_suite(repo)
    recorded: list[dict] = []

    class _Project:
        project_root = repo

        def create(self, **kwargs):
            recorded.append({"root": str(repo), **kwargs})
            return {"id": "rec-suite", "subject": kwargs.get("subject")}

    monkeypatch.setattr(suite, "open_store", lambda directory: _Project())
    code, out, err = run(
        [
            "suite",
            "record",
            "--cwd",
            str(repo),
            "--phase",
            "p1",
            "--effort",
            "packaging",
        ],
        capsys,
    )
    assert code == 0, err
    assert json.loads(out)["record"]["id"] == "rec-suite"
    assert len(recorded) == 1
    created = recorded[0]
    assert created["record_type"] == "tuner:check-run"
    assert created["subject"] == "p1-suite"
    assert created["payload"]["result"] == "pass"
    assert created["payload"]["effort"] == "packaging"
    assert created["payload"]["evidence_kind"] == "integration"
    assert "1 passed" in created["body"]


def _store_repo(tmp_path: Path) -> Path:
    repo = make_git_repo()
    assert make_design(repo).is_file()
    git(repo, "add", ".canon")
    git(repo, "commit", "-qm", "store")
    return repo


def test_store_path_smoke(tmp_path, capsys):
    repo = _store_repo(tmp_path)
    code, out, err = run(["store", "path", "--cwd", str(repo), "--json"], capsys)
    assert code == 0, err
    target = json.loads(out)
    from orchestra.canon.project import open_store

    project = open_store(repo)
    assert target["store"] == str(project.store_path)
    assert target["binding"] == project.binding.location

    code, out, err = run(["store", "path", "--cwd", str(repo)], capsys)
    assert code == 0
    assert out.strip() == str(repo / ".canon")


def test_store_run_smoke(tmp_path, monkeypatch, capsys):
    repo = _store_repo(tmp_path)
    calls: list[str] = []

    class _Project:
        def list(self, record_type: str):
            calls.append(record_type)
            return []

    monkeypatch.setattr(cli, "open_store", lambda directory: _Project())
    code, out, err = run(
        ["store", "run", "--cwd", str(repo), "--", "list", "--type", "score:work-item"],
        capsys,
    )
    assert code == 0, err
    assert json.loads(out) == {"records": [], "count": 0}
    assert calls == ["score:work-item"]


def test_store_ensure_creates_a_canon_store_once(tmp_path, capsys):
    fresh = make_git_repo()
    code, out, err = run(["store", "ensure", "--cwd", str(fresh), "--json"], capsys)
    assert code == 0, err
    ensured = json.loads(out)
    config = Path(ensured["store"]) / "config.json"
    assert ensured["store_ready"] is True
    assert set(json.loads(config.read_text())["schemas"]) == {"score", "conductor", "tuner"}

    config.write_text(json.dumps({"format": "canon/1", "schemas": {}, "settings": {"kept": True}}))
    code, out, err = run(["store", "ensure", "--cwd", str(fresh)], capsys)
    assert code == 0, err
    assert json.loads(config.read_text())["settings"] == {"kept": True}
