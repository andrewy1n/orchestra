"""Phase-end commands resolve the store from --store, then ORCHESTRA_STORE, then cwd."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import REPO_ROOT, copy_store, git, make_git_repo, run_cli
from test_analyze import SLUG, seed_phase
from test_check import _seed_acceptance
from test_gate import PHASE as GATE_PHASE
from test_gate import seed as seed_gate

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


def _set_suite_policy(store: Path, command: str) -> None:
    config_path = store / ".canon" / "config.json"
    config = json.loads(config_path.read_text())
    config.setdefault("settings", {})["conductor"] = {
        "phase_gate": {"suite": {"mode": "smoke", "command": command, "gate": "advisory"}}
    }
    config_path.write_text(json.dumps(config))


def _check_runs(store: Path) -> list[dict]:
    result = run_cli("list", "--type", "tuner:check-run", root=store)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["records"]


def _write_finished_suite(repo: Path) -> None:
    suite_dir = repo / ".suite"
    suite_dir.mkdir()
    (suite_dir / f"{SESSION}.log").write_text("1 passed\n")
    (suite_dir / f"{SESSION}.exit").write_text("0\n")
    (repo / ".gitignore").write_text(".suite/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "ignore suite")


def _suite_record_args(repo: Path) -> list[str]:
    return [
        "suite",
        "record",
        "--phase",
        PHASE,
        "--effort",
        "resolve-effort",
        "--session",
        SESSION,
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


def test_suite_store_flag(store, code_repo, home):
    _set_suite_policy(store, "echo from-store")
    result = _orchestra(
        "suite", "policy", "--cwd", str(code_repo), "--store", str(store), cwd=code_repo, home=home
    )
    assert result.returncode == 0, result.stdout + result.stderr
    policy = json.loads(result.stdout)
    assert policy["command"] == "echo from-store"


def test_suite_store_flag_start(store, code_repo, home):
    _set_suite_policy(store, "")
    result = _orchestra(
        "suite",
        "start",
        "--phase",
        PHASE,
        "--cwd",
        str(code_repo),
        "--store",
        str(store),
        cwd=code_repo,
        home=home,
        extra_env={"PATH": os.environ["PATH"]},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    document = json.loads(result.stdout)
    assert document["state"] == "skipped"
    assert document["policy"]["mode"] == "smoke"


def test_suite_store_flag_record(store, cli, resolved_contract, code_repo, home):
    _seed_suite_effort(store, cli, resolved_contract)
    _write_finished_suite(code_repo)
    result = _orchestra(
        *_suite_record_args(code_repo), "--store", str(store), cwd=code_repo, home=home
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]


def test_env_fallback_suite(store, cli, resolved_contract, code_repo, home):
    _set_suite_policy(store, "echo from-env")
    policy = _orchestra(
        "suite",
        "policy",
        "--cwd",
        str(code_repo),
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert policy.returncode == 0, policy.stdout + policy.stderr
    assert json.loads(policy.stdout)["command"] == "echo from-env"

    _seed_suite_effort(store, cli, resolved_contract)
    _write_finished_suite(code_repo)
    record = _orchestra(
        *_suite_record_args(code_repo),
        cwd=code_repo,
        home=home,
        extra_env={"ORCHESTRA_STORE": str(store)},
    )
    assert record.returncode == 0, record.stdout + record.stderr
    assert [run["subject"] for run in _check_runs(store)] == [f"{PHASE}-suite"]


def test_cwd_fallback_suite(store, cli, resolved_contract, home):
    _set_suite_policy(store, "echo from-cwd")
    policy = _orchestra("suite", "policy", cwd=store, home=home)
    assert policy.returncode == 0, policy.stdout + policy.stderr
    assert json.loads(policy.stdout)["command"] == "echo from-cwd"

    _seed_suite_effort(store, cli, resolved_contract)
    _write_finished_suite(store)
    record = _orchestra(*_suite_record_args(store), cwd=store, home=home)
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
    result = _run_with_canon_store(
        ["gate", SLUG], via=via, store=store, third=third, repo=repo, home=home
    )
    assert "missing" in result.stdout, result.stdout + result.stderr
    assert "not found" not in result.stdout + result.stderr


def _do_land(via, store, third, cli, contract, repo, home) -> None:
    seed_phase(cli, contract)
    result = _run_with_canon_store(
        ["land", SLUG], via=via, store=store, third=third, repo=repo, home=home
    )
    assert "missing" in result.stderr, result.stdout + result.stderr
    assert "not found" not in result.stderr


def _do_suite_policy(via, store, third, cli, contract, repo, home) -> None:
    _set_suite_policy(store, "echo from-store")
    args = ["suite", "policy", "--cwd", str(repo)]
    result = _run_with_canon_store(args, via=via, store=store, third=third, repo=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["command"] == "echo from-store"


def _do_suite_start(via, store, third, cli, contract, repo, home) -> None:
    _set_suite_policy(store, "")
    args = ["suite", "start", "--phase", PHASE, "--cwd", str(repo)]
    result = _run_with_canon_store(args, via=via, store=store, third=third, repo=repo, home=home)
    assert result.returncode == 0, result.stdout + result.stderr
    document = json.loads(result.stdout)
    assert document["state"] == "skipped"
    assert document["policy"]["mode"] == "smoke"


def _do_suite_record(via, store, third, cli, contract, repo, home) -> None:
    _seed_suite_effort(store, cli, contract)
    _write_finished_suite(repo)
    result = _run_with_canon_store(
        _suite_record_args(repo), via=via, store=store, third=third, repo=repo, home=home
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


def test_canon_store_does_not_override_flag_suite_policy(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_policy("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_suite_policy(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_policy("env", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_flag_suite_start(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_start("flag", store, third_store, cli, resolved_contract, code_repo, home)


def test_canon_store_does_not_override_env_suite_start(
    store, third_store, cli, resolved_contract, code_repo, home
):
    _do_suite_start("env", store, third_store, cli, resolved_contract, code_repo, home)


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


def test_subprocess_keeps_canon_store_land(store, third_store, cli, home, tmp_path):
    seen = tmp_path / "seen.txt"
    seed_gate(store, cli, landing_lines=(f'- merge: `printf %s "$CANON_STORE" > {seen}`',))
    third = str(third_store / ".canon")
    result = _orchestra(
        "land",
        GATE_PHASE,
        "--store",
        str(store),
        cwd=store,
        home=home,
        extra_env={"CANON_STORE": third},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert seen.read_text() == third


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
