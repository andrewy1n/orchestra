from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import pytest
from conftest import make_task

from orchestra.canon.errors import ReadOnlyStoreError
from orchestra.canon.project import Project
from orchestra.canon.workspace import Access, StoreNotReady, Workspace

T = TypeVar("T")


def _attempt(call: Callable[[], T]) -> tuple[T | None, Exception | None]:
    try:
        return call(), None
    except Exception as exc:
        return None, exc


def _store_of(workspace: Workspace) -> Path:
    project, error = _attempt(workspace.open)
    assert error is None, repr(error)
    assert project is not None
    return project.store_path


def test_same_store_for_same_start_dir(project: Project, repo: Path) -> None:
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    first = _store_of(Workspace.resolve(nested))
    second = _store_of(Workspace.resolve(nested))
    assert first == second == project.store_path


def test_same_store_walks_up_from_nested_start(project: Project, repo: Path) -> None:
    nested = repo / "deep" / "er"
    nested.mkdir(parents=True)
    assert Workspace.resolve(nested).root == repo.resolve()


def test_same_store_explicit_arg_beats_env_and_walk(
    project: Project, repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("ORCHESTRA_STORE", str(other))
    nested = repo / "sub"
    nested.mkdir()
    assert Workspace.resolve(nested, store=repo).root == repo


def test_same_store_env_beats_walk(
    project: Project, repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("ORCHESTRA_STORE", str(other))
    assert Workspace.resolve(repo).root == other


def test_access_read_workspace_opens_read_only(project: Project, repo: Path) -> None:
    opened, error = _attempt(Workspace.resolve(repo, access=Access.READ).open)
    assert error is None, repr(error)
    assert opened is not None
    assert opened.read_only is True


def test_access_write_on_read_workspace_raises_and_changes_nothing(
    project: Project, repo: Path
) -> None:
    before = len(project.records())
    opened, error = _attempt(Workspace.resolve(repo, access=Access.READ).open)
    assert error is None, repr(error)
    assert opened is not None
    _, write_error = _attempt(lambda: make_task(opened, "blocked"))
    assert isinstance(write_error, ReadOnlyStoreError)
    assert len(project.records()) == before


def test_access_write_workspace_opens_writable(project: Project, repo: Path) -> None:
    opened, error = _attempt(Workspace.resolve(repo, access=Access.WRITE).open)
    assert error is None, repr(error)
    assert opened is not None
    assert opened.read_only is False
    make_task(opened, "allowed")


def test_not_ready_when_no_store_carries_searched_paths(tmp_path: Path) -> None:
    start = tmp_path / "empty" / "child"
    start.mkdir(parents=True)
    _, error = _attempt(lambda: Workspace.resolve(start).open())
    assert isinstance(error, StoreNotReady), repr(error)
    assert start.resolve() in error.searched
    assert start.resolve().parent in error.searched


def test_not_ready_for_explicit_store_that_does_not_exist(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    _, error = _attempt(lambda: Workspace.resolve(tmp_path, store=missing).open())
    assert isinstance(error, StoreNotReady), repr(error)
    assert missing in error.searched
