"""Phase-end commands resolve the store from --store, then ORCHESTRA_STORE, then cwd."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import REPO_ROOT, copy_store, git, make_git_repo, run_cli
from test_analyze import SLUG, seed_phase
from test_check import _seed_acceptance
from test_gate import write_policy

from orchestra import store as store_module

PHASE = "resolve-phase"
DIFF_LINE = "code-repo-only-line"
SESSION = "resolve-suite-session"


def _orchestra(
    *args: str, cwd: Path, home: Path, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"ORCHESTRA_STORE", "CANON_STORE"}
    }
    env["HOME"] = str(home)
    env["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys([str(REPO_ROOT), *filter(None, [env.get("PYTHONPATH")])])
    )
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


@pytest.fixture
def home(tmp_path: Path) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    return path


@pytest.fixture
def third_store(store_template: Path) -> Iterator[Path]:
    root = copy_store(store_template)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def code_repo() -> Path:
    repo = make_git_repo()
    (repo / "code.txt").write_text(f"{DIFF_LINE}\n")
    git(repo, "add", "code.txt")
    git(repo, "commit", "-qm", "code")
    return repo


def _check_runs(store: Path) -> list[dict]:
    result = run_cli("list", "--type", "tuner:check-run", root=store)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["records"]


def _start_finished_suite(repo: Path, home: Path) -> str:
    if not (repo / "orchestra.toml").is_file():
        write_policy(repo, mode="full", command="true")
    started = _orchestra(
        "suite",
        "start",
        "--phase",
        PHASE,
        "--session",
        SESSION,
        "--cwd",
        str(repo),
        "--command",
        "printf '1 passed\\n'",
        "--allow-dirty",
        cwd=repo,
        home=home,
    )
    assert started.returncode == 0, started.stdout + started.stderr
    run_id = json.loads(started.stdout)["run_id"]
    poll_args = (
        "suite",
        "poll",
        "--phase",
        PHASE,
        "--session",
        SESSION,
        "--cwd",
        str(repo),
        "--run-id",
        run_id,
        "--allow-dirty",
    )
    deadline = time.monotonic() + 5
    result = _orchestra(*poll_args, cwd=repo, home=home)
    while json.loads(result.stdout).get("state") == "running" and time.monotonic() < deadline:
        time.sleep(0.02)
        result = _orchestra(*poll_args, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["result"] == "pass"
    return run_id


def _suite_record_args(repo: Path, run_id: str) -> list[str]:
    return [
        "suite",
        "record",
        "--phase",
        PHASE,
        "--effort",
        "resolve-effort",
        "--session",
        SESSION,
        "--run-id",
        run_id,
        "--allow-dirty",
        "--cwd",
        str(repo),
    ]


def _seed_suite_effort(store: Path, cli, resolved_contract) -> None:
    import helpers as h

    defs = h.record_defs_by_id(resolved_contract)
    h.create_generic_record(cli, defs, "score:effort", subject="resolve-effort")
    git(store, "add", "-A")
    git(store, "commit", "-qm", "seed")


def test_resolve_store_prefers_the_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_STORE", str(tmp_path / "env"))
    assert store_module.resolve_store(str(tmp_path / "flag"), tmp_path) == tmp_path / "flag"


def test_resolve_store_uses_env_when_flag_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_STORE", str(tmp_path / "env"))
    assert store_module.resolve_store(None, tmp_path) == tmp_path / "env"


def test_resolve_store_ignores_an_empty_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_STORE", "")
    assert store_module.resolve_store(None, tmp_path) == tmp_path.resolve()


def test_review_brief_store_flag(store, cli, resolved_contract, code_repo, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra(
        "review-brief",
        "--cwd",
        str(code_repo),
        "--store",
        str(store),
        "--base",
        "HEAD~1",
        cwd=code_repo,
        home=home,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{SLUG}-wi-r1" in result.stdout
    assert DIFF_LINE in result.stdout


def test_env_fallback_review_brief(store, cli, resolved_contract, code_repo, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra(
        "review-brief",
        "--base",
        "HEAD~1",
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{SLUG}-wi-r1" in result.stdout
    assert DIFF_LINE in result.stdout


def test_cwd_fallback_review_brief(store, cli, resolved_contract, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra("review-brief", "--base", "HEAD", cwd=store, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{SLUG}-wi-r1" in result.stdout


def test_suite_store_flag_record(store, cli, resolved_contract, code_repo, home):
    _seed_suite_effort(store, cli, resolved_contract)
    run_id = _start_finished_suite(code_repo, home)
    result = _orchestra(
        *_suite_record_args(code_repo, run_id), "--store", str(store), cwd=code_repo, home=home
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]


def test_env_fallback_suite(store, cli, resolved_contract, code_repo, home):
    _seed_suite_effort(store, cli, resolved_contract)
    run_id = _start_finished_suite(code_repo, home)
    record = _orchestra(
        *_suite_record_args(code_repo, run_id),
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert record.returncode == 0, record.stdout + record.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]


def test_cwd_fallback_suite(store, cli, resolved_contract, home):
    _seed_suite_effort(store, cli, resolved_contract)
    run_id = _start_finished_suite(store, home)
    record = _orchestra(*_suite_record_args(store, run_id), cwd=store, home=home)
    assert record.returncode == 0, record.stdout + record.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]


def _check_args(acceptance: dict, code_repo: Path) -> list[str]:
    return ["check", "--acceptance", acceptance["id"], "--cwd", str(code_repo)]


def _seed_check(store: Path, cli, resolved_contract) -> dict:
    return _seed_acceptance(
        store, cli, resolved_contract, subject="resolve-check", verify_command="true"
    )


def test_check_store_flag(store, cli, resolved_contract, code_repo, home):
    acceptance = _seed_check(store, cli, resolved_contract)
    result = _orchestra(
        *_check_args(acceptance, code_repo), "--store", str(store), cwd=code_repo, home=home
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == ["resolve-check"]


def test_env_fallback_check(store, cli, resolved_contract, code_repo, home):
    acceptance = _seed_check(store, cli, resolved_contract)
    result = _orchestra(
        *_check_args(acceptance, code_repo),
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == ["resolve-check"]


def test_cwd_fallback_check(store, cli, resolved_contract, code_repo, home):
    acceptance = _seed_check(store, cli, resolved_contract)
    result = _orchestra(*_check_args(acceptance, code_repo), cwd=store, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == ["resolve-check"]


def test_analyze_store_flag(store, cli, resolved_contract, code_repo, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra(
        "analyze",
        SLUG,
        "--json",
        "--cwd",
        str(code_repo),
        "--store",
        str(store),
        cwd=code_repo,
        home=home,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["phase"] == SLUG


def test_env_fallback_analyze(store, cli, resolved_contract, code_repo, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra(
        "analyze",
        SLUG,
        "--json",
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["phase"] == SLUG


def test_cwd_fallback_analyze(store, cli, resolved_contract, home):
    seed_phase(cli, resolved_contract)
    result = _orchestra("analyze", SLUG, "--json", cwd=store, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["phase"] == SLUG


def _run_with_canon_store(
    args: list[str], *, via: str, store: Path, third: Path, repo: Path, home: Path
) -> subprocess.CompletedProcess[str]:
    env = {"CANON_STORE": str(third / ".canon"), "PATH": os.environ["PATH"]}
    if via == "flag":
        args = [*args, "--store", str(store)]
    else:
        env["ORCHESTRA_STORE"] = str(store)
    return _orchestra(*args, cwd=repo, home=home, extra_env=env)


def _do_review_brief(via, store, third, cli, contract, repo, home) -> None:
    seed_phase(cli, contract)
    args = ["review-brief", "--cwd", str(repo), "--base", "HEAD~1"]
    result = _run_with_canon_store(args, via=via, store=store, third=third, repo=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{SLUG}-wi-r1" in result.stdout


def _do_analyze(via, store, third, cli, contract, repo, home) -> None:
    seed_phase(cli, contract)
    args = ["analyze", SLUG, "--json", "--cwd", str(repo)]
    result = _run_with_canon_store(args, via=via, store=store, third=third, repo=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["phase"] == SLUG


def _do_check(via, store, third, cli, contract, repo, home) -> None:
    acceptance = _seed_check(store, cli, contract)
    args = _check_args(acceptance, repo)
    result = _run_with_canon_store(args, via=via, store=store, third=third, repo=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == ["resolve-check"]
    assert _check_runs(third) == []


def _do_gate(via, store, third, cli, contract, repo, home) -> None:
    seed_phase(cli, contract)
    write_policy(store)
    result = _run_with_canon_store(
        ["gate", SLUG], via=via, store=store, third=third, repo=repo, home=home
    )
    assert "missing" in result.stdout, result.stdout + result.stderr
    assert "not found" not in result.stdout + result.stderr


def _do_land(via, store, third, cli, contract, repo, home) -> None:
    seed_phase(cli, contract)
    write_policy(repo)
    result = _run_with_canon_store(
        ["land", "--phase", SLUG, "--cwd", str(repo)],
        via=via,
        store=store,
        third=third,
        repo=repo,
        home=home,
    )
    assert result.returncode == 5, result.stdout + result.stderr
    assert "verification-task-done" in result.stderr, result.stdout + result.stderr
    assert "not found" not in result.stderr


def _do_suite_record(via, store, third, cli, contract, repo, home) -> None:
    _seed_suite_effort(store, cli, contract)
    run_id = _start_finished_suite(repo, home)
    result = _run_with_canon_store(
        _suite_record_args(repo, run_id),
        via=via,
        store=store,
        third=third,
        repo=repo,
        home=home,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]
    assert _check_runs(third) == []


def test_canon_store_does_not_override_flag_review_brief(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_review_brief("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_review_brief(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_review_brief("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_analyze(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_analyze("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_analyze(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_analyze("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_check(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_check("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_check(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_check("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_gate(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_gate("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_gate(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_gate("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_land(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_land("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_land(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_land("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_suite_record(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_record("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_suite_record(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_record("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_subprocess_keeps_canon_store_check(
    store, third_store, cli, resolved_contract, code_repo, home, tmp_path
):
    seen = tmp_path / "seen.txt"
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="resolve-check",
        verify_command=f'printf %s "$CANON_STORE" > {seen}',
    )
    third = str(third_store / ".canon")
    result = _orchestra(
        *_check_args(acceptance, code_repo),
        "--store",
        str(store),
        cwd=code_repo,
        home=home,
        extra_env={"CANON_STORE": third},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert seen.read_text() == third
    assert [run["subject"] for run in _check_runs(store)] == ["resolve-check"]


def test_canon_store_still_applies_without_flag_or_env(
    store, cli, resolved_contract, code_repo, home
):
    seed_phase(cli, resolved_contract)
    result = _orchestra(
        "analyze",
        SLUG,
        "--json",
        cwd=code_repo,
        home=home,
        extra_env={"CANON_STORE": str(store / ".canon")},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["phase"] == SLUG


def test_check_help_names_process_cwd(home):
    result = _orchestra("check", "--help", cwd=REPO_ROOT, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    text = " ".join(result.stdout.split())
    assert "then resolve from the process cwd" in text
    assert "then resolve from --cwd" not in text
