"""The CLI exposes the reviewer, suite, and store surface skills call by name.

A skill must be able to run the phase-end reviewer, the contracted suite, and
store-bound ``adaptive-artifacts`` calls with ``orchestra`` alone. These tests
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

from orchestra import cli  # noqa: E402
from orchestra import suite  # noqa: E402

# Every runtime call a skill makes must be one of these named commands.
HELP_PATHS = [
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
    design = path / ".artifacts" / "project-design.json"
    design.parent.mkdir(parents=True, exist_ok=True)
    body: dict = {"project": "orchestra"}
    if suite_policy is not None:
        body["phase_gate"] = {"suite": suite_policy}
    design.write_text(json.dumps(body))
    return design


def finished_suite(work: Path, phase: str = "p1", exit_code: str = "0") -> None:
    directory = work / ".suite"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"orchestra-suite-{phase}.log").write_text(
        "1 passed in 0.01s\n"
    )
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
    for name in ("review-brief", "suite", "store"):
        assert name in text


def test_review_brief_smoke(tmp_path, monkeypatch, capsys):
    records = [
        {
            "record_type": "project:work-item",
            "subject": "tabs",
            "title": "Implement tabs",
            "body": "Implement the status tabs.",
        },
        {
            "record_type": "project:acceptance",
            "subject": "tabs",
            "criterion": "Tabs render both filters.",
        },
        {
            "record_type": "project:requirement",
            "subject": "R6",
            "title": "R6",
            "body": "Name commands, not modules.",
        },
        {
            "record_type": "project:execution-report",
            "subject": "tabs",
            "body": "SECRET_BUILDER_NOTES",
        },
    ]
    calls: list[tuple[str, ...]] = []

    def fake_run_aa(*args: str, root: Path, **kwargs):
        calls.append(args)
        return completed(args, json.dumps({"records": records}))

    monkeypatch.setattr("orchestra.aa.run_aa", fake_run_aa)
    monkeypatch.setattr(
        "orchestra.reviewer.git_phase_diff", lambda *a, **k: "+reviewed line"
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
    assert calls and all("--full" in args for args in calls)


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
        "orchestra.suite.start_suite_background", lambda **kwargs: started
    )
    code, out, err = run(
        ["suite", "start", "--cwd", str(work), "--phase", "p1"], capsys
    )
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
    code, out, err = run(
        ["suite", "poll", "--cwd", str(repo), "--phase", "p1"], capsys
    )
    assert code == 3
    assert json.loads(out)["state"] == "running"

    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    finished_suite(repo)
    code, out, err = run(
        ["suite", "poll", "--cwd", str(repo), "--phase", "p1"], capsys
    )
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
    code, out, err = run(
        ["suite", "collect", "--cwd", str(repo), "--phase", "p1"], capsys
    )
    assert code == 1
    result = json.loads(out)
    assert result["result"] == "fail"
    assert result["failing_node_ids"] == ["tests/test_foo.py::test_bar"]


def test_suite_record_smoke(tmp_path, monkeypatch, capsys):
    repo = _git_worktree()
    finished_suite(repo)
    recorded: list[dict] = []

    def fake_create(root, **kwargs):
        recorded.append({"root": str(root), **kwargs})
        return {"id": "rec-suite", "subject": kwargs.get("subject")}

    monkeypatch.setattr("orchestra.aa.create_record", fake_create)
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
    assert created["record_type"] == "project:check-run"
    assert created["subject"] == "p1-suite"
    assert created["payload"]["result"] == "pass"
    assert created["payload"]["effort"] == "packaging"
    assert created["payload"]["evidence_kind"] == "integration"
    assert "1 passed" in created["body"]


def _store_repo(tmp_path: Path) -> Path:
    repo = make_git_repo()
    design = make_design(repo)
    (repo / ".artifacts" / "meta.json").write_text(
        json.dumps({"contract": "project-design.json"})
    )
    git(repo, "add", ".artifacts")
    git(repo, "commit", "-qm", "store")
    assert design.is_file()
    return repo


def test_store_path_smoke(tmp_path, capsys):
    repo = _store_repo(tmp_path)
    code, out, err = run(["store", "path", "--cwd", str(repo), "--json"], capsys)
    assert code == 0, err
    target = json.loads(out)
    assert target["store"] == str(repo / ".artifacts")
    assert target["contract"] == str(repo / ".artifacts" / "project-design.json")
    assert target["binding"] == "local"

    code, out, err = run(["store", "path", "--cwd", str(repo)], capsys)
    assert code == 0
    assert out.strip() == str(repo / ".artifacts")


def test_store_run_smoke(tmp_path, monkeypatch, capsys):
    repo = _store_repo(tmp_path)
    calls: list[tuple[str, ...]] = []

    def fake_run_aa(*args: str, root: Path, **kwargs):
        calls.append(args)
        return completed(args, "pong\n")

    monkeypatch.setattr("orchestra.aa.run_aa", fake_run_aa)
    code, out, err = run(
        ["store", "run", "--cwd", str(repo), "--", "list", "--type", "project:work-item"],
        capsys,
    )
    assert code == 0, err
    assert out.strip() == "pong"
    assert calls == [("list", "--type", "project:work-item")]


def test_store_ensure_writes_a_design_once(tmp_path, capsys):
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    code, out, err = run(["store", "ensure", "--cwd", str(fresh), "--json"], capsys)
    assert code == 0, err
    ensured = json.loads(out)
    design = Path(ensured["design"])
    assert design.is_file()
    assert design.read_text() == (REPO_ROOT / "contract" / "project-design.json").read_text()
    assert ensured["store_ready"] is False

    # An existing design is never overwritten.
    design.write_text('{"project": "someone-else"}')
    code, out, err = run(["store", "ensure", "--cwd", str(fresh)], capsys)
    assert code == 0, err
    assert design.read_text() == '{"project": "someone-else"}'
