"""orchestra.aa passes --store/--contract from store binding resolve."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import make_git_repo
from orchestra import aa, aa_resolve


def _meta(store: Path) -> Path:
    store.mkdir(parents=True, exist_ok=True)
    contract = store / "resolved-contract.json"
    contract.write_text(json.dumps({"views": []}))
    (store / "meta.json").write_text(
        json.dumps({"store_version": 1, "contract": str(contract), "contract_digest": "sha256:test"})
    )
    return contract


@pytest.fixture()
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SE_WORKFLOW_STORE", raising=False)
    return home


def test_run_aa_passes_bound_store_and_contract(home, tmp_path):
    repo = make_git_repo()
    _meta(repo / ".artifacts")
    (home / ".artifacts" / repo.name).mkdir(parents=True)
    _meta(home / ".artifacts" / repo.name)
    (repo / ".artifacts" / "store-binding.json").write_text(json.dumps({"store": "local"}))

    recorded: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd and cmd[0] == "aa":
            recorded.append(list(cmd))

            class Result:
                returncode = 0
                stdout = "{}"
                stderr = ""

            return Result()
        return real_run(cmd, *args, **kwargs)

    with patch.object(aa, "resolve_aa_command", return_value=["aa"]), patch(
        "orchestra.aa.subprocess.run", side_effect=fake_run
    ):
        aa.run_aa("list", "--type", "project:active-goal", root=repo)

    assert recorded, "aa subprocess.run was not called"
    cmd = recorded[0]
    assert cmd[:1] == ["aa"]
    assert "--root" in cmd
    assert Path(cmd[cmd.index("--root") + 1]).resolve() == repo.resolve()
    store_idx = cmd.index("--store")
    assert Path(cmd[store_idx + 1]).resolve() == (repo / ".artifacts").resolve()
    assert "--contract" in cmd


def test_run_aa_raises_when_binding_points_at_missing_store(home):
    repo = make_git_repo()
    _meta(home / ".artifacts" / repo.name)
    (repo / ".artifacts").mkdir(parents=True, exist_ok=True)
    (repo / ".artifacts" / "store-binding.json").write_text(json.dumps({"store": "local"}))
    with pytest.raises(aa_resolve.StoreBindingError):
        aa.run_aa("list", root=repo)


def test_aa_py_does_not_mention_dashboard():
    source = (Path(__file__).resolve().parents[1] / "orchestra" / "aa.py").read_text()
    assert "dashboard" not in source
