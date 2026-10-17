"""Store binding resolution: local | global, exclusive, layered preference."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import make_git_repo
from dashboard import artifact_store as a


def _meta(store: Path, contract: Path | None = None) -> None:
    store.mkdir(parents=True, exist_ok=True)
    contract = contract or (store / "resolved-contract.json")
    if not contract.is_file():
        contract.write_text(json.dumps({"views": [{"id": "project:dashboard"}]}))
    (store / "meta.json").write_text(
        json.dumps({"store_version": 1, "contract": str(contract), "contract_digest": "sha256:test"})
    )


def _binding(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"store": value}))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture()
def repo():
    return make_git_repo()


def test_default_prefers_local_when_both_have_meta(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    target = a.resolve(repo, env={})
    assert Path(target.store).resolve() == (repo / ".artifacts").resolve()
    assert target.binding is not None and target.binding.store == "local"
    assert target.binding.source == "default"


def test_default_uses_global_when_only_home_has_meta(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(home / ".artifacts" / repo.name)
    target = a.resolve(repo, env={})
    assert Path(target.store).resolve() == (home / ".artifacts" / repo.name).resolve()
    assert target.binding is not None and target.binding.store == "global"


def test_committed_local_wins_over_home_store(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / a.COMMITTED_BINDING, "local")
    target = a.resolve(repo, env={})
    assert Path(target.store).resolve() == (repo / ".artifacts").resolve()
    assert target.binding is not None
    assert target.binding.source.endswith(a.COMMITTED_BINDING)


def test_local_override_beats_committed(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / a.COMMITTED_BINDING, "local")
    _binding(repo / ".artifacts" / a.LOCAL_BINDING, "global")
    target = a.resolve(repo, env={})
    assert Path(target.store).resolve() == (home / ".artifacts" / repo.name).resolve()
    assert target.binding is not None and target.binding.store == "global"


def test_env_beats_local_override(home, repo):
    _meta(repo / ".artifacts")
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / a.LOCAL_BINDING, "global")
    target = a.resolve(repo, env={a.ENV_STORE: "local"})
    assert Path(target.store).resolve() == (repo / ".artifacts").resolve()
    assert target.binding is not None and target.binding.source == f"env:{a.ENV_STORE}"

def test_bound_missing_store_raises_without_fallthrough(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(home / ".artifacts" / repo.name)
    _binding(repo / ".artifacts" / a.COMMITTED_BINDING, "local")
    with pytest.raises(a.StoreBindingError, match="no meta.json"):
        a.resolve(repo, env={})


def test_invalid_binding_value_raises(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(repo / ".artifacts")
    (repo / ".artifacts" / a.COMMITTED_BINDING).write_text(json.dumps({"store": "both"}))
    with pytest.raises(a.StoreBindingError, match="local"):
        a.resolve(repo, env={})


def test_invalid_env_raises(home, repo):
    _meta(repo / ".artifacts")
    with pytest.raises(a.StoreBindingError, match="SE_WORKFLOW_STORE"):
        a.resolve(repo, env={a.ENV_STORE: "both"})


def test_cli_args_include_store_and_contract(home, repo, monkeypatch):
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    _meta(repo / ".artifacts")
    args = a.resolve(repo, env={}).cli_args()
    assert args[0] == "--root" and Path(args[1]).resolve() == repo.resolve()
    assert args[2] == "--store" and Path(args[3]).resolve() == (repo / ".artifacts").resolve()
    assert args[4] == "--contract"
