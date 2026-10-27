"""bin/aff verdict does not need the runtime on PATH; check/close-batch are not aff verbs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from test_verdict import AFF, APP_GREEN, APP_RED, CLAIM, _repo


def _path_without_runtime() -> str:
    kept: list[str] = []
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        executable = Path(entry) / "canon"
        if executable.is_file() and os.access(executable, os.X_OK):
            continue
        kept.append(entry)
    return os.pathsep.join(kept)


def test_verdict_without_runtime(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN, branch=True)
    env = os.environ.copy()
    env["PATH"] = _path_without_runtime()
    proc = subprocess.run(
        [str(AFF), "verdict", "--at", head, CLAIM],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_rejects_store_commands() -> None:
    for command in ("check", "close-batch"):
        proc = subprocess.run(
            [str(AFF), command, "--help"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, command


def test_verdict_help() -> None:
    proc = subprocess.run(
        [str(AFF), "verdict", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
