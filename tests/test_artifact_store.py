"""Store opening follows canon.project.open_store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.project import StoreBindingError, open_store
from conftest import make_git_repo, write_config


def _meta(store: Path) -> None:
    write_config(store)


def _binding(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"store": value}))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ARTIFACTS_STORE", raising=False)
    return home


@pytest.fixture()
def repo():
    return make_git_repo()


def test_default_prefers_local_when_both_have_meta(home, repo):
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    project = open_store(repo)
    assert project.store_path.resolve() == (repo / ".artifacts").resolve()
    assert project.binding.location == "local"
    assert project.binding.source == "default"


def test_default_uses_global_when_only_home_has_meta(home, repo):
    _meta(home / ".artifacts" / repo.name)
    project = open_store(repo)
    assert project.store_path.resolve() == (home / ".artifacts" / repo.name).resolve()
    assert project.binding.location == "global"


def test_committed_local_wins_over_home_store(home, repo):
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / "store-binding.json", "local")
    project = open_store(repo)
    assert project.store_path.resolve() == (repo / ".artifacts").resolve()
    assert project.binding.source.endswith("store-binding.json")


def test_local_override_beats_committed(home, repo):
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / "store-binding.json", "local")
    _binding(repo / ".artifacts" / "store-binding.local.json", "global")
    project = open_store(repo)
    assert project.store_path.resolve() == (home / ".artifacts" / repo.name).resolve()
    assert project.binding.location == "global"


def test_explicit_store_argument_beats_binding(home, repo):
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / "store-binding.local.json", "global")
    project = open_store(repo, store=repo / ".artifacts")
    assert project.store_path.resolve() == (repo / ".artifacts").resolve()
    assert project.binding.source == "argument"


def test_bound_missing_store_raises_without_fallthrough(home, repo):
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / "store-binding.json", "local")
    with pytest.raises(StoreBindingError, match="no config.json"):
        open_store(repo)


def test_invalid_binding_value_raises(home, repo):
    _meta(repo / ".artifacts")
    (repo / ".artifacts" / "store-binding.json").write_text(json.dumps({"store": "both"}))
    with pytest.raises(StoreBindingError, match="local"):
        open_store(repo)


def test_open_store_exposes_project_root(home, repo):
    _meta(repo / ".artifacts")
    project = open_store(repo)
    assert project.project_root.resolve() == repo.resolve()
