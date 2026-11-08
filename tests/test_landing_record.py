from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_gate import PHASE, Cli, Phase, _land_args, _packet, _review_repo_head, seed

from orchestra.canon.types import Record
from orchestra.cli import main as cli_main
from orchestra.conductor import land

URL = "https://github.com/owner/repo/pull/7"


@pytest.fixture
def phase(store: Path, cli: Cli) -> Phase:
    return seed(store, cli)


def _dispatch_returning(
    monkeypatch: pytest.MonkeyPatch, result: str, check: land.LandingCheck
) -> None:
    def dispatch(root: Path, proof_packet: str, **kwargs: object) -> land.LandingResult:
        del root, proof_packet, kwargs
        return land.LandingResult(result, 7, URL, "f" * 40, (check,), ())

    monkeypatch.setattr(land, "dispatch_land", dispatch)


def _landing_records(phase: Phase) -> list[Record]:
    result = phase.cli("list", "--type", "conductor:landing", "--subject", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    records: list[Record] = json.loads(result.stdout)["records"]
    return records


def test_land_writes_landing_record_when_ci_passes(
    phase: Phase, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dispatch_returning(monkeypatch, "success", land.LandingCheck("CI", "completed", "success"))
    _review_repo_head(phase)
    _packet(phase)

    assert cli_main(_land_args(phase)) == 0

    [record] = _landing_records(phase)
    assert record["payload"]["phase"] == PHASE
    assert record["payload"]["number"] == 7
    assert record["payload"]["url"] == URL
    assert record["payload"]["head_sha"] == "f" * 40
    assert record["payload"]["result"] == "success"


def test_land_writes_landing_record_when_ci_fails(
    phase: Phase, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dispatch_returning(monkeypatch, "fail", land.LandingCheck("CI", "completed", "failure"))
    _review_repo_head(phase)
    _packet(phase)

    assert cli_main(_land_args(phase)) == 1

    [record] = _landing_records(phase)
    assert record["payload"]["result"] == "fail"
    assert record["payload"]["number"] == 7


def test_each_land_run_adds_a_landing_record(phase: Phase, monkeypatch: pytest.MonkeyPatch) -> None:
    _review_repo_head(phase)
    _packet(phase)
    _dispatch_returning(monkeypatch, "fail", land.LandingCheck("CI", "completed", "failure"))
    assert cli_main(_land_args(phase)) == 1
    _dispatch_returning(monkeypatch, "success", land.LandingCheck("CI", "completed", "success"))
    assert cli_main(_land_args(phase)) == 0

    records = _landing_records(phase)

    assert sorted(str(record["payload"]["result"]) for record in records) == ["fail", "success"]


def test_a_gate_failure_writes_no_landing_record(
    phase: Phase, monkeypatch: pytest.MonkeyPatch
) -> None:
    _dispatch_returning(monkeypatch, "success", land.LandingCheck("CI", "completed", "success"))

    assert cli_main(_land_args(phase)) == 5

    assert _landing_records(phase) == []


def test_landing_record_is_registered_in_the_synced_store_schema() -> None:
    from conftest import REPO_ROOT

    source = json.loads(
        (REPO_ROOT / "orchestra/conductor/schemas/conductor.json").read_text(encoding="utf-8")
    )
    synced = json.loads((REPO_ROOT / ".canon/schemas/conductor.json").read_text(encoding="utf-8"))

    assert "landing" in source["types"]
    assert synced["types"]["landing"] == source["types"]["landing"]
