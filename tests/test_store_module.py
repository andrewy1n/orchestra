"""Workspace.resolve finds and opens the bound store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import make_git_repo, write_config

from orchestra.canon.project import open_store
from orchestra.canon.workspace import StoreNotReady, Workspace


def _meta(store: Path) -> Path:
    return write_config(store)


@pytest.fixture()
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CANON_STORE", raising=False)
    return home


def test_resolve_finds_the_bound_store_root(home):
    repo = make_git_repo()
    _meta(repo / ".canon")
    _meta(home / ".canon" / repo.name)
    (repo / ".canon" / "store-binding.json").write_text(json.dumps({"store": "local"}))
    project = open_store(repo)
    assert project.store_path.resolve() == (repo / ".canon").resolve()
    assert Workspace.resolve(repo).root.resolve() == repo.resolve()


def test_resolve_raises_when_binding_points_at_missing_store(home):
    repo = make_git_repo()
    _meta(home / ".canon" / repo.name)
    (repo / ".canon").mkdir(parents=True, exist_ok=True)
    (repo / ".canon" / "store-binding.json").write_text(json.dumps({"store": "local"}))
    with pytest.raises(StoreNotReady):
        Workspace.resolve(repo)
