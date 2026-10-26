"""orchestra.aa opens the store through canon.project.open_store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.project import StoreBindingError, open_store
from conftest import make_git_repo, write_config
from orchestra import aa


def _meta(store: Path) -> Path:
    return write_config(store)


@pytest.fixture()
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ARTIFACTS_STORE", raising=False)
    return home


def test_get_record_reads_the_bound_store(home):
    repo = make_git_repo()
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    (repo / ".artifacts" / "store-binding.json").write_text(json.dumps({"store": "local"}))
    project = open_store(repo)
    assert project.store_path.resolve() == (repo / ".artifacts").resolve()
    assert aa.find_store_root(repo).resolve() == repo.resolve()


def test_open_store_raises_when_binding_points_at_missing_store(home):
    repo = make_git_repo()
    _meta(home / ".artifacts" / repo.name)
    (repo / ".artifacts").mkdir(parents=True, exist_ok=True)
    (repo / ".artifacts" / "store-binding.json").write_text(json.dumps({"store": "local"}))
    with pytest.raises(StoreBindingError):
        open_store(repo)
    with pytest.raises(StoreBindingError):
        aa.get_record(repo, "rec-missing")


def test_aa_py_does_not_mention_dashboard():
    source = (Path(__file__).resolve().parents[1] / "orchestra" / "aa.py").read_text()
    assert "dashboard" not in source
