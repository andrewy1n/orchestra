"""Cursor install merges hooks.json instead of replacing it."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRA_HOOK_PREFIX = "orchestra hook-"


def run_cursor_install(project: Path, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), env.get("PYTHONPATH", "")]).strip(
        os.pathsep
    )
    env["ORCHESTRA_INSTALL_SOURCE"] = str(REPO_ROOT)
    env["HOME"] = str(home)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.cli",
            "install",
            "--only",
            "cursor",
            "--home",
            str(home),
            *args,
        ],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def prepared_home(tmp_path: Path) -> tuple[Path, Path, Path]:
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    cursor_root = home / ".cursor"
    cursor_root.mkdir(parents=True)
    return project, home, cursor_root / "hooks.json"


def load_object(text: str) -> dict[str, object]:
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise AssertionError("expected a JSON object")
    document: dict[str, object] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise AssertionError("expected string keys")
        document[key] = value
    return document


def read_document(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    return load_object(path.read_text(encoding="utf-8"))


def write_document(path: Path, document: dict[str, object]) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def user_document() -> dict[str, object]:
    session_start: dict[str, object] = {"command": "user-session-start", "timeout": 9}
    prompt: dict[str, object] = {"command": "user-prompt"}
    return {
        "version": 1,
        "hooks": {
            "sessionStart": [session_start],
            "beforeSubmitPrompt": [prompt],
        },
    }


def payload_document() -> dict[str, object]:
    return load_object((REPO_ROOT / "hosts" / "cursor" / "hooks.json").read_text(encoding="utf-8"))


def string_keyed(entry: dict[object, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in entry.items():
        if isinstance(key, str):
            normalized[key] = value
    return normalized


def entries_by_event(document: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    hooks = document.get("hooks")
    if not isinstance(hooks, dict):
        return {}
    grouped: dict[str, list[dict[str, object]]] = {}
    for event, entries in hooks.items():
        if not isinstance(event, str) or not isinstance(entries, list):
            continue
        collected: list[dict[str, object]] = []
        for entry in entries:
            if isinstance(entry, dict):
                collected.append(string_keyed(entry))
        grouped[event] = collected
    return grouped


def commands_by_event(document: dict[str, object]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, tuple[str, ...]] = {}
    for event, entries in entries_by_event(document).items():
        commands: list[str] = []
        for entry in entries:
            command = entry.get("command")
            if isinstance(command, str):
                commands.append(command)
        grouped[event] = tuple(commands)
    return grouped


def hook_commands(document: dict[str, object]) -> list[str]:
    commands: list[str] = []
    for grouped in commands_by_event(document).values():
        commands.extend(grouped)
    return commands


def command_sets_by_event(document: dict[str, object]) -> dict[str, set[str]]:
    return {event: set(commands) for event, commands in commands_by_event(document).items()}


def merged_sets(user: dict[str, object], payload: dict[str, object]) -> dict[str, set[str]]:
    user_sets = command_sets_by_event(user)
    payload_sets = command_sets_by_event(payload)
    events = list(user_sets)
    for event in payload_sets:
        if event not in events:
            events.append(event)
    return {
        event: set(user_sets.get(event, ())) | set(payload_sets.get(event, ())) for event in events
    }


def link_user_hooks(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, bytes, dict[str, object]]:
    project, home, hooks = prepared_home(tmp_path)
    target = tmp_path / "dotfiles" / "hooks.json"
    target.parent.mkdir(parents=True)
    user = user_document()
    write_document(target, user)
    original = target.read_bytes()
    hooks.symlink_to(target)
    return project, home, hooks, target, original, user


def symlink_target(path: Path) -> Path:
    linked = Path(os.readlink(path))
    if linked.is_absolute():
        return linked
    return path.parent / linked


def sync_plugin_needle() -> str:
    return "".join(("sync-", "plugin"))


def test_install_adds_orchestra_hooks(tmp_path: Path) -> None:
    project, home, hooks = prepared_home(tmp_path)
    user = user_document()
    write_document(hooks, user)
    proc = run_cursor_install(project, home, "--copy")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert command_sets_by_event(read_document(hooks)) == merged_sets(user, payload_document())


def test_install_keeps_user_hooks(tmp_path: Path) -> None:
    project, home, hooks = prepared_home(tmp_path)
    user = user_document()
    write_document(hooks, user)
    proc = run_cursor_install(project, home, "--copy")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = entries_by_event(read_document(hooks))
    for event, entries in entries_by_event(user).items():
        actual = installed.get(event, [])
        for entry in entries:
            assert entry in actual


def test_second_install_changes_nothing(tmp_path: Path) -> None:
    project, home, hooks = prepared_home(tmp_path)
    user = user_document()
    write_document(hooks, user)
    first = run_cursor_install(project, home, "--copy")
    assert first.returncode == 0, first.stdout + first.stderr
    before = hooks.read_bytes()
    second = run_cursor_install(project, home, "--copy")
    assert second.returncode == 0, second.stdout + second.stderr
    assert hooks.read_bytes() == before
    assert command_sets_by_event(read_document(hooks)) == merged_sets(user, payload_document())


def test_uninstall_removes_only_orchestra_hooks(tmp_path: Path) -> None:
    project, home, hooks = prepared_home(tmp_path)
    user = user_document()
    write_document(hooks, user)
    installed = run_cursor_install(project, home, "--copy")
    assert installed.returncode == 0, installed.stdout + installed.stderr
    removed = run_cursor_install(project, home, "--copy", "--uninstall")
    assert removed.returncode == 0, removed.stdout + removed.stderr
    remaining = read_document(hooks)
    for event, entries in entries_by_event(user).items():
        actual = entries_by_event(remaining).get(event, [])
        for entry in entries:
            assert entry in actual
    for command in hook_commands(payload_document()):
        assert command not in hook_commands(remaining)


def test_payload_only_orchestra_commands() -> None:
    rejected = [
        command
        for command in hook_commands(payload_document())
        if not command.startswith(ORCHESTRA_HOOK_PREFIX)
    ]
    assert rejected == []


def test_symlink_replaced_with_regular_file(tmp_path: Path) -> None:
    project, home, hooks, _target, _original, user = link_user_hooks(tmp_path)
    proc = run_cursor_install(project, home)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert hooks.is_symlink() is False
    assert hooks.is_file() is True
    assert command_sets_by_event(read_document(hooks)) == merged_sets(user, payload_document())


def test_symlink_target_unchanged(tmp_path: Path) -> None:
    project, home, hooks, target, original, user = link_user_hooks(tmp_path)
    proc = run_cursor_install(project, home)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert target.read_bytes() == original
    if hooks.is_symlink():
        assert symlink_target(hooks).read_bytes() == original
    assert command_sets_by_event(read_document(hooks)) == merged_sets(user, payload_document())


def test_sync_plugin_script_absent() -> None:
    script = REPO_ROOT / "scripts" / "".join(("sync-", "plugin.sh"))
    assert script.exists() is False


def test_no_sync_plugin_references() -> None:
    proc = subprocess.run(
        ["git", "grep", "-n", sync_plugin_needle()],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.stdout == ""
