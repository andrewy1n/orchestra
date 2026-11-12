from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from test_wave_end import _land, _world  # pyright: ignore[reportPrivateUsage]

import orchestra.tuner.manifest as manifest
from orchestra.canon.git_backend import GitContextError, git_root
from orchestra.canon.project_config import CONFIG_PATH
from orchestra.conductor import wave
from orchestra.tools import Git
from orchestra.tuner.manifest import ManifestError, resolve_commit
from orchestra.tuner.plugin_evidence import _config_digest  # pyright: ignore[reportPrivateUsage]


def _timing_out(argv: Sequence[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    if list(argv)[1:] == ["--version"]:
        return subprocess.CompletedProcess(list(argv), 0, "git version 2.40.0\n", "")
    raise subprocess.TimeoutExpired(list(argv), 5.0)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def test_manifest_reports_timeout_cause(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manifest, "Git", lambda cwd: Git(cwd, run=_timing_out))  # pyright: ignore[reportArgumentType]
    with pytest.raises(ManifestError) as info:
        resolve_commit(tmp_path, "HEAD")
    assert "timed out" in str(info.value)
    assert "not available" not in str(info.value)


def test_git_root_reports_timeout_cause(tmp_path: Path) -> None:
    with pytest.raises(GitContextError) as info:
        git_root(tmp_path, run=_timing_out)  # pyright: ignore[reportArgumentType]
    assert "timed out" in str(info.value)
    assert "not found" not in str(info.value)


def test_wave_end_raises_when_branch_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _world(tmp_path, {"a": "true"})
    _land(project, repo, "a", "a.txt", "a\n")
    original = Git.resolve

    def resolve(self: Git, rev: str) -> str | None:
        if rev == "task/ph/a":
            return None
        return original(self, rev)

    monkeypatch.setattr(Git, "resolve", resolve)
    with pytest.raises(wave.WaveError, match="task/ph/a"):
        wave.end(project, repo, "ph")


def test_plugin_config_digest_matches_text_mode(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "core.autocrlf", "false")
    (tmp_path / CONFIG_PATH).write_bytes(b"a = 1\r\nb = 2\r\n")
    _git(tmp_path, "add", CONFIG_PATH)
    _git(tmp_path, "commit", "-qm", "c")
    expected = "sha256:" + hashlib.sha256(b"a = 1\nb = 2\n").hexdigest()
    assert _config_digest(tmp_path, "HEAD") == expected
