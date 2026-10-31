from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from orchestra.canon.backend import open_backend
from orchestra.canon.config import new_config
from orchestra.canon.modules import discover
from orchestra.canon.project import open_store
from orchestra.canon.revision import with_revision
from orchestra.stage import hooks

ROOT = Path(__file__).resolve().parents[2]
EFFORT_ID = "rec-00000000-0000-4000-8000-000000000001"


def _record(
    record_id: str, record_type: str, subject: str, payload: dict[str, Any]
) -> dict[str, Any]:
    return with_revision(
        {
            "id": record_id,
            "record_type": record_type,
            "subject": subject,
            "payload": payload,
            "lifecycle_state": "active",
            "relationships": {},
            "body": "",
            "recorded_at": "2026-01-01T00:00:00+00:00",
        }
    )


def _global_sqlite_repo(root: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root.mkdir(parents=True)
    metadata = root / ".canon"
    metadata.mkdir()
    installed = discover()
    namespaces = ("score", "conductor", "tuner", "composer")
    config = new_config({name: installed[name].version for name in namespaces})
    config["backend"] = "sqlite"
    (metadata / "config.json").write_text(json.dumps(config))
    (metadata / "store-binding.json").write_text('{"store":"global"}\n')
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    backend = open_backend(metadata)
    for namespace in namespaces:
        backend.write_snapshot(namespace, installed[namespace].text)
    backend.create_record(
        _record(
            EFFORT_ID,
            "score:effort",
            "cutover-effort",
            {"goal": "Read the global database", "kind": "deliver"},
        )
    )
    return root


def test_cutover_r9_worktree_reads_primary_global_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    primary = _global_sqlite_repo(tmp_path / "primary", tmp_path / "home", monkeypatch)
    subprocess.run(["git", "init", str(primary)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(primary), "config", "user.email", "test@example.invalid"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(primary), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "-C", str(primary), "add", ".canon"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(primary), "commit", "-m", "seed"],
        check=True,
        capture_output=True,
    )
    worktree = tmp_path / "secondary"
    subprocess.run(
        [
            "git",
            "-C",
            str(primary),
            "worktree",
            "add",
            str(worktree),
            "-b",
            "secondary",
        ],
        check=True,
        capture_output=True,
    )
    primary_record = open_store(primary).get(EFFORT_ID)
    try:
        secondary_record = open_store(worktree).get(EFFORT_ID)
    except Exception:
        secondary_record = None
    assert secondary_record == primary_record


def test_cutover_r10_handoff_reads_efforts_from_the_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _global_sqlite_repo(tmp_path / "repo", tmp_path / "home", monkeypatch)
    monkeypatch.chdir(root)
    from orchestra import cli

    assert cli.main(["handoff"]) == 0
    assert "cutover-effort" in capsys.readouterr().out


def test_cutover_r11_dashboard_api_returns_efforts_from_the_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi.routing import APIRoute
    from dashboard.backend.server.app import create_app

    root = _global_sqlite_repo(tmp_path / "repo", tmp_path / "home", monkeypatch)
    app = create_app(open_store(root))
    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == "/api/snapshot"
    )
    response = route.endpoint()
    assert [row.effort for row in response.efforts] == ["cutover-effort"]


def _run_start_hook(root: Path) -> None:
    hooks.cmd_start(hooks.CLAUDE, {"cwd": str(root), "session_id": "cutover"})


def _backup_calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []
    original_run = subprocess.run

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command = args[0]
        if isinstance(command, list) and command[:2] == ["canon", "backup"]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_cutover_r12_session_start_runs_backup_after_24_hours(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _global_sqlite_repo(tmp_path / "repo", tmp_path / "home", monkeypatch)
    backup_dir = tmp_path / "home" / ".canon" / "repo" / "backups"
    backup_dir.mkdir(parents=True)
    old = backup_dir / "old.json"
    old.write_text("backup")
    os.utime(old, (time.time() - 25 * 60 * 60, time.time() - 25 * 60 * 60))
    calls = _backup_calls(monkeypatch)
    _run_start_hook(root)
    assert len(calls) == 1


def test_cutover_r13_session_start_skips_backup_within_24_hours(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _global_sqlite_repo(tmp_path / "repo", tmp_path / "home", monkeypatch)
    backup_dir = tmp_path / "home" / ".canon" / "repo" / "backups"
    backup_dir.mkdir(parents=True)
    fresh = backup_dir / "fresh.json"
    fresh.write_text("backup")
    os.utime(fresh, (time.time() - 1 * 60 * 60, time.time() - 1 * 60 * 60))
    calls = _backup_calls(monkeypatch)
    _run_start_hook(root)
    assert calls == []


def test_cutover_r14_agents_does_not_instruct_store_commits_on_work_branch() -> None:
    guidance = (ROOT / "AGENTS.md").read_text().lower()
    assert "commit store changes on the same branch" not in guidance
    assert "commit store changes on your work branch" not in guidance


def test_cutover_r15_agents_does_not_require_primary_checkout_for_canon() -> None:
    guidance = (ROOT / "AGENTS.md").read_text().lower()
    assert "run `canon` from the primary checkout root" not in guidance


def test_cutover_r16_agents_states_database_location() -> None:
    guidance = (ROOT / "AGENTS.md").read_text().lower()
    assert ".canon/<repo-name>/canon.db" in guidance


def test_cutover_r17_agents_names_backup_command() -> None:
    guidance = (ROOT / "AGENTS.md").read_text().lower()
    assert "canon backup" in guidance


def test_cutover_r18_ensure_store_describes_database() -> None:
    guidance = (ROOT / "skills" / "ensure-store.md").read_text().lower()
    assert "sqlite" in guidance
    assert "database" in guidance


def test_cutover_r19_generated_skills_are_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_skills.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cutover_r20_ci_does_not_read_the_live_store() -> None:
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    jobs = workflow["jobs"]
    commands = [str(step.get("run", "")) for job in jobs.values() for step in job.get("steps", [])]
    assert not any("canon validate" in command for command in commands)


def test_cutover_r1_config_selects_sqlite() -> None:
    config = json.loads((ROOT / ".canon" / "config.json").read_text())
    assert config.get("backend") == "sqlite"


def test_cutover_r2_binding_selects_global_store() -> None:
    binding = json.loads((ROOT / ".canon" / "store-binding.json").read_text())
    assert binding == {"store": "global"}


def test_cutover_r3_tracked_canon_contents_are_metadata_only() -> None:
    result = subprocess.run(
        ["git", "ls-files", ".canon"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [Path(line).relative_to(".canon").as_posix() for line in result.stdout.splitlines()]
    assert tracked
    assert all(
        path in {"config.json", "store-binding.json"} or path.startswith("schemas/")
        for path in tracked
    )


def test_cutover_r4_gitignore_ignores_legacy_store_trees() -> None:
    for path in (
        ".canon/log/cutover.ops",
        ".canon/records/cutover.md",
        ".canon/history/cutover.md",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"{path} is not ignored"


def test_cutover_r21_production_code_has_no_file_backend_imports() -> None:
    forbidden_layout_functions = {
        "append_resolved_op",
        "prune_before",
        "purge_chain",
        "read_ops",
    }
    roots = (ROOT / "orchestra", ROOT / "dashboard", ROOT / "scripts")
    violations: list[str] = []
    for base in roots:
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported = {alias.name for alias in node.names}
                    if node.module and node.module.endswith(".store") and "Store" in imported:
                        violations.append(f"{path}: imports Store")
                    if node.module and node.module.endswith(".record_file"):
                        violations.append(f"{path}: imports record_file")
                    if node.module and node.module.endswith(".oplog"):
                        used = imported & forbidden_layout_functions
                        if used:
                            violations.append(f"{path}: imports {sorted(used)}")
                elif isinstance(node, ast.Import):
                    if any(alias.name.endswith(".record_file") for alias in node.names):
                        violations.append(f"{path}: imports record_file")
    assert violations == []
