"""orchestra verify assertion-red and verdict stay on run_verdict, store-free (R7–R10)."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
from pathlib import Path

from orchestra.tuner.cli import main
from orchestra.tuner.oracle_red import is_assertion_level_red
from orchestra.tuner.verdict import run_verdict
from test_oracle_red import (
    ASSERTION_FAIL_TAIL,
    IMPORT_FAIL_TAIL,
    NODE_ASSERT,
    NODE_IMPORT_COLLECT,
)
from test_verdict import VERIFY, APP_GREEN, APP_RED, CLAIM, _repo

import orchestra.tuner.cli as cli_mod


def _tuner_assertion_red(record: dict) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    return subprocess.run(
        [*VERIFY, "assertion-red"],
        input=json.dumps(record),
        capture_output=True,
        text=True,
        env=env,
    )


def test_verdict_gate_assertion_red_exits_zero() -> None:
    """R7: orchestra verify assertion-red exits 0 when is_assertion_level_red is true."""
    record = {
        "result": "fail",
        "failing_node_ids": [NODE_ASSERT],
        "body": ASSERTION_FAIL_TAIL,
    }
    assert is_assertion_level_red(record) is True
    proc = _tuner_assertion_red(record)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_verdict_gate_assertion_red_exits_one() -> None:
    """R8: orchestra verify assertion-red exits 1 when is_assertion_level_red is false."""
    record = {
        "result": "fail",
        "failing_node_ids": [NODE_IMPORT_COLLECT],
        "body": IMPORT_FAIL_TAIL,
    }
    assert is_assertion_level_red(record) is False
    proc = _tuner_assertion_red(record)
    assert proc.returncode == 1, proc.stdout + proc.stderr


def _arm_store_spy(monkeypatch) -> list[str]:
    opened: list[str] = []

    def spy_open(*args, **kwargs):
        opened.append("open_store")
        raise RuntimeError("artifact store opened")

    def spy_method(name: str):
        def _inner(*args, **kwargs):
            opened.append(name)
            raise RuntimeError("artifact store opened")

        return _inner

    try:
        project_mod = importlib.import_module("orchestra.canon.project")
    except ImportError:
        project_mod = None
    if project_mod is not None:
        monkeypatch.setattr(project_mod, "open_store", spy_open)
        monkeypatch.setattr(project_mod.Project, "create", spy_method("create"))
        monkeypatch.setattr(project_mod.Project, "list", spy_method("list"))
        monkeypatch.setattr(project_mod.Project, "get", spy_method("get"))

    import orchestra.tuner.binding as binding_mod
    import orchestra.tuner.observation as observation_mod
    import orchestra.tuner.verdict as verdict_mod

    for module in (verdict_mod, observation_mod, binding_mod, cli_mod):
        if hasattr(module, "open_store"):
            monkeypatch.setattr(module, "open_store", spy_open)
        project_cls = getattr(module, "Project", None)
        if project_cls is not None:
            monkeypatch.setattr(project_cls, "create", spy_method("create"), raising=False)
            monkeypatch.setattr(project_cls, "list", spy_method("list"), raising=False)
            monkeypatch.setattr(project_cls, "get", spy_method("get"), raising=False)
    return opened


def test_verdict_gate_command_calls_run_verdict(tmp_path: Path, monkeypatch, capsys) -> None:
    """R9: orchestra verify verdict calls run_verdict without opening an artifact store to decide the gate."""
    root = tmp_path / "repo"
    base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN)
    assert not (root / ".canon").exists()
    opened = _arm_store_spy(monkeypatch)
    seen: dict = {}
    real = cli_mod.run_verdict

    def wrapped(cwd, at, base_rev, claim_ids, provenance=False):
        seen["before"] = list(opened)
        result = real(cwd, at, base_rev, claim_ids, provenance=provenance)
        seen["during"] = list(opened)
        seen["result"] = result
        seen["cwd"] = str(cwd)
        seen["at"] = at
        seen["claim_ids"] = list(claim_ids)
        return result

    monkeypatch.setattr(cli_mod, "run_verdict", wrapped)
    code = main(["verdict", "--cwd", str(root), "--base", base, "--at", head, CLAIM])
    captured = capsys.readouterr()
    assert seen.get("result"), "orchestra verify verdict calls run_verdict"
    assert seen["before"] == []
    assert seen["during"] == []
    assert seen["claim_ids"] == [CLAIM]
    assert Path(seen["cwd"]) == root
    assert seen["at"] == head
    assert code == (0 if seen["result"]["result"] == "pass" else 1)
    assert json.loads(captured.out)["result"] == seen["result"]["result"]


def test_verdict_gate_without_store(tmp_path: Path, monkeypatch) -> None:
    """R10: run_verdict returns a verdict for a repository that has no artifact store."""
    root = tmp_path / "repo"
    base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN)
    assert not (root / ".canon").exists()
    opened = _arm_store_spy(monkeypatch)
    try:
        payload = run_verdict(root, head, base, [CLAIM])
    except Exception as exc:
        raise AssertionError(
            "run_verdict returns a verdict for a repository that has no artifact store"
        ) from exc
    assert isinstance(payload, dict)
    assert payload.get("result") == "pass"
    assert isinstance(payload.get("claims"), list) and payload["claims"]
    assert opened == []
    assert not (root / ".canon").exists()
