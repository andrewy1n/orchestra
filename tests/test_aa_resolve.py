"""Store opening goes through adaptive_artifacts.project.open_store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adaptive_artifacts.project import StoreBindingError, open_store
from conftest import make_git_repo
from orchestra import aa


def _meta(store: Path) -> None:
    store.mkdir(parents=True, exist_ok=True)
    contract = store / "resolved-contract.json"
    contract.write_text(json.dumps({"records": []}))
    (store / "meta.json").write_text(
        json.dumps({"store_version": 1, "contract": str(contract), "contract_digest": "sha256:test"})
    )


def test_open_store_prefers_local_meta(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ARTIFACTS_STORE", raising=False)
    repo = make_git_repo()
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    project = open_store(repo)
    assert project.store_path.resolve() == (repo / ".artifacts").resolve()
    assert project.binding.location == "local"
    assert aa.find_store_root(repo).resolve() == repo.resolve()


def test_open_store_uses_global_when_only_home_has_meta(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ARTIFACTS_STORE", raising=False)
    repo = make_git_repo()
    _meta(home / ".artifacts" / repo.name)
    project = open_store(repo)
    assert project.store_path.resolve() == (home / ".artifacts" / repo.name).resolve()
    assert project.binding.location == "global"


def test_missing_store_raises(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ARTIFACTS_STORE", raising=False)
    repo = make_git_repo()
    with pytest.raises(StoreBindingError):
        open_store(repo)
