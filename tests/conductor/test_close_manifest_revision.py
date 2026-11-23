from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_task_close_decision import (
    CLAIM,
    Scenario,
    _approved,
    _check_run,
    _check_scenario,
    _commit,
    _decide,
    _entry,
    _reason,
    _tuner_outcomes,
)

from orchestra.canon.types import Record
from orchestra.tuner.plugins.manifest import DEFAULT_RUNNER

_TOML = (
    f'[verify.stages]\nphase = ["unit"]\n\n[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n'
)


def _manifest_text(claim_id: str) -> str:
    claim = {"id": claim_id, "text": "t", "tests": ["tests/test_x.py::test_x"], "oracle_hashes": {}}
    return json.dumps({"claims": [claim]})


def _commit_manifest(s: Scenario, claim_id: str) -> tuple[str, Record]:
    _commit(s.git, s.root, "orchestra.toml", _TOML.encode(), "config")
    sha = _commit(s.git, s.root, ".tuner/manifest.json", _manifest_text(claim_id).encode(), "m")
    run = _check_run(s.project, s.aid, "check", {"revision": sha})
    return sha, run


def test_r7_refuses_a_claim_listed_only_in_an_uncommitted_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    (s.root / ".tuner").mkdir()
    (s.root / ".tuner" / "manifest.json").write_text(_manifest_text(CLAIM), encoding="utf-8")
    _tuner_outcomes(monkeypatch, "pass", "pass")

    reason = _reason(_decide(s))

    assert reason == "claim manifest is missing"


def test_r7_accepts_a_claim_listed_in_the_committed_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    _, run = _commit_manifest(s, CLAIM)
    _tuner_outcomes(monkeypatch, "pass", "pass")

    _approved(_decide(s, _entry(s, check_run_id=run["id"])))


def test_r7_refuses_a_claim_the_committed_manifest_does_not_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    _, run = _commit_manifest(s, "claim-other")
    _tuner_outcomes(monkeypatch, "pass", "pass")

    reason = _reason(_decide(s, _entry(s, check_run_id=run["id"])))

    assert reason == f"criterion {s.aid!r}: claim {CLAIM!r} is not listed in .tuner/manifest.json"
