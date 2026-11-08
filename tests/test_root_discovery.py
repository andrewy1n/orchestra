from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NoReturn

import pytest

import orchestra.canon.project as project
import orchestra.cli as cli
from orchestra.tools import Git, ToolError


def _missing(
    argv: Sequence[str],
    *,
    cwd: Path,
    input: str | None,
    timeout: float | None,
    capture_output: bool,
    text: bool,
    check: bool,
    env: Mapping[str, str] | None,
) -> NoReturn:
    raise FileNotFoundError("git")


def _old_git(
    argv: Sequence[str],
    *,
    cwd: Path,
    input: str | None,
    timeout: float | None,
    capture_output: bool,
    text: bool,
    check: bool,
    env: Mapping[str, str] | None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(argv), 0, "git version 2.1.0\n", "")


def _patch(monkeypatch: pytest.MonkeyPatch, module: object, run: Callable[..., object]) -> None:
    monkeypatch.setattr(module, "Git", lambda directory: Git(directory, run=run))  # pyright: ignore[reportArgumentType]


def test_cli_git_root_raises_when_git_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch, cli, _missing)

    with pytest.raises(ToolError):
        cli._git_root(tmp_path)  # pyright: ignore[reportPrivateUsage]


def test_cli_git_root_raises_when_git_is_too_old(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch, cli, _old_git)

    with pytest.raises(ToolError):
        cli._git_root(tmp_path)  # pyright: ignore[reportPrivateUsage]


def test_cli_git_root_falls_back_outside_a_repository(tmp_path: Path) -> None:
    assert cli._git_root(tmp_path) == tmp_path.resolve()  # pyright: ignore[reportPrivateUsage]


def test_project_root_raises_when_git_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch, project, _missing)

    with pytest.raises(ToolError):
        project._project_root(tmp_path)  # pyright: ignore[reportPrivateUsage]


def test_project_root_falls_back_outside_a_repository(tmp_path: Path) -> None:
    assert project._project_root(tmp_path) == tmp_path.resolve()  # pyright: ignore[reportPrivateUsage]


def test_cli_git_root_falls_back_for_a_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "nowhere"

    assert cli._git_root(missing) == missing.resolve()  # pyright: ignore[reportPrivateUsage]


def test_project_root_falls_back_for_a_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "nowhere"

    assert project._project_root(missing) == missing.resolve()  # pyright: ignore[reportPrivateUsage]
