"""orchestra verify verdict does not need the runtime on PATH; check/close-batch are not aff verbs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from test_verdict import VERIFY, APP_GREEN, APP_RED, CLAIM, _repo


def _path_without_runtime(shim_dir: Path) -> str:
    kept: list[str] = [str(shim_dir)]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        executable = Path(entry) / "canon"
        if executable.is_file() and os.access(executable, os.X_OK):
            continue
        kept.append(entry)
    return os.pathsep.join(kept)


def _python_shim(shim_dir: Path) -> None:
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    shim.chmod(0o755)


def test_verdict_without_runtime(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN, branch=True)
    shim_dir = tmp_path / "shim"
    _python_shim(shim_dir)
    env = os.environ.copy()
    env["PATH"] = _path_without_runtime(shim_dir)
    proc = subprocess.run(
        [*VERIFY, "verdict", "--at", head, CLAIM],
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_rejects_store_commands() -> None:
    for command in ("check", "close-batch"):
        proc = subprocess.run(
            [*VERIFY, command, "--help"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, command


def test_verdict_help() -> None:
    proc = subprocess.run(
        [*VERIFY, "verdict", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
