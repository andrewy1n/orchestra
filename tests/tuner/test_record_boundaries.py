from __future__ import annotations

from pathlib import Path

import pytest

from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.types import Record
from orchestra.canon.validation import ValidationError
from orchestra.tuner.binding import BindingError, active_for_claim, bind_observation, list_bindings
from orchestra.tuner.observation import (
    maybe_record_observation,
    maybe_record_verdict_observation,
    record_observation,
)

STORE_FAILURES = (
    ("binding", "Invalid store binding JSON"),
    ("config", "malformed JSON in config.json"),
    ("selected", "has no config.json"),
)


def _break_store(store: Path, fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CANON_STORE", raising=False)
    if fault == "binding":
        (store / ".canon" / "store-binding.json").write_text("{", encoding="utf-8")
    elif fault == "config":
        (store / ".canon" / "config.json").write_text("{", encoding="utf-8")
    elif fault == "selected":
        monkeypatch.setenv("CANON_STORE", str(store / "missing"))
    else:
        raise AssertionError(f"unknown store fault: {fault}")


def _seed_observation(root: Path) -> Record:
    return open_store(root).create(
        record_type="tuner:evidence-observation",
        subject="existing-observation",
        payload={
            "technique": "verdict",
            "base_rev": "base-pin",
            "head_rev": "head-pin",
            "result": "pass",
            "claim_ids": ["claim-widget"],
        },
    )


def test_binding_returns_persisted_record(store: Path) -> None:
    observation = _seed_observation(store)
    record = bind_observation(
        store,
        observation_id=observation["id"],
        claim_id="claim-widget",
        base_rev="base-pin",
        head_rev="head-pin",
    )

    assert record["record_type"] == "tuner:evidence-binding"
    assert record["payload"] == {
        "observation_id": observation["id"],
        "claim_id": "claim-widget",
        "base_rev": "base-pin",
        "head_rev": "head-pin",
    }
    assert record["revision"].startswith("sha256:")
    assert open_store(store).get(record["id"]) == record


def test_observation_returns_persisted_record(store: Path) -> None:
    record = record_observation(
        store,
        technique="verdict",
        base_rev="base-pin",
        head_rev="head-pin",
        result="pass",
        claim_ids=["claim-widget"],
        replay="repeat-verdict",
    )

    assert record is not None
    assert record["record_type"] == "tuner:evidence-observation"
    assert record["payload"] == {
        "technique": "verdict",
        "base_rev": "base-pin",
        "head_rev": "head-pin",
        "result": "pass",
        "claim_ids": ["claim-widget"],
        "replay": "repeat-verdict",
    }
    assert record["revision"].startswith("sha256:")
    assert open_store(store).get(record["id"]) == record


def test_invalid_binding_preserves_canon_diagnostic(store: Path) -> None:
    observation = _seed_observation(store)
    with pytest.raises(BindingError, match="subject must be a non-empty slug") as error:
        bind_observation(
            store,
            observation_id=observation["id"],
            claim_id="invalid claim",
            base_rev="base-pin",
            head_rev="head-pin",
        )

    cause = error.value.__cause__
    assert isinstance(cause, ValidationError)
    assert str(error.value) == str(cause)


def test_invalid_observation_preserves_canon_diagnostic(store: Path) -> None:
    with pytest.raises(RuntimeError, match="subject must be a non-empty slug") as error:
        record_observation(
            store,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
            subject="invalid subject",
        )

    cause = error.value.__cause__
    assert isinstance(cause, ValidationError)
    assert str(error.value) == str(cause)


def test_rejected_binding_leaves_store_unchanged(store: Path) -> None:
    observation = _seed_observation(store)
    project = open_store(store)
    before = project.records()

    with pytest.raises(BindingError):
        bind_observation(
            store,
            observation_id=observation["id"],
            claim_id="invalid claim",
            base_rev="base-pin",
            head_rev="head-pin",
        )

    assert project.records() == before


def test_rejected_observation_leaves_store_unchanged(store: Path) -> None:
    _seed_observation(store)
    project = open_store(store)
    before = project.records()

    with pytest.raises(RuntimeError):
        record_observation(
            store,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
            subject="invalid subject",
        )

    assert project.records() == before


def test_observation_without_usable_store_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("CANON_STORE", raising=False)

    assert (
        record_observation(
            tmp_path,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
        )
        is None
    )
    assert list_bindings(tmp_path) == []
    assert active_for_claim(tmp_path, "claim-widget") == []
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(("fault", "diagnostic"), STORE_FAILURES)
def test_strict_observation_raises_for_invalid_stores(
    store: Path, fault: str, diagnostic: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _break_store(store, fault, monkeypatch)

    with pytest.raises((StoreBindingError, RuntimeError), match=diagnostic):
        record_observation(
            store,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
        )


@pytest.mark.parametrize(("fault", "diagnostic"), STORE_FAILURES)
@pytest.mark.parametrize("reader", ["list", "active"])
def test_binding_reads_raise_for_invalid_stores(
    store: Path,
    fault: str,
    diagnostic: str,
    reader: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _break_store(store, fault, monkeypatch)

    with pytest.raises(BindingError, match=diagnostic):
        if reader == "list":
            list_bindings(store)
        else:
            active_for_claim(store, "claim-widget")


@pytest.mark.parametrize(("fault", "diagnostic"), STORE_FAILURES)
def test_binding_writes_preserve_invalid_store_diagnostics(
    store: Path, fault: str, diagnostic: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _break_store(store, fault, monkeypatch)

    with pytest.raises(BindingError, match=diagnostic):
        bind_observation(
            store,
            observation_id="existing-observation",
            claim_id="claim-widget",
            base_rev="base-pin",
            head_rev="head-pin",
        )


@pytest.mark.parametrize(("fault", "diagnostic"), STORE_FAILURES)
@pytest.mark.parametrize("record_verdict", [False, True])
def test_optional_recording_reports_invalid_stores_once(
    store: Path,
    fault: str,
    diagnostic: str,
    record_verdict: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _break_store(store, fault, monkeypatch)

    if record_verdict:
        recorded = maybe_record_verdict_observation(
            store, at="HEAD", base="HEAD", claim_ids=(), result="pass"
        )
    else:
        recorded = maybe_record_observation(
            store,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
        )

    captured = capsys.readouterr()
    assert recorded is False
    assert captured.out == ""
    assert captured.err.startswith("observation record skipped: ")
    assert diagnostic in captured.err
    assert len(captured.err.splitlines()) == 1


def test_best_effort_observation_reports_canon_failure(
    store: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = open_store(store).records()

    maybe_record_observation(
        store,
        technique="verdict",
        base_rev="base-pin",
        head_rev="head-pin",
        result="pass",
        subject="invalid subject",
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("observation record skipped: ")
    assert "subject must be a non-empty slug" in captured.err
    assert open_store(store).records() == before


def test_optional_observation_reports_unreadable_store(
    store: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (store / ".canon" / "config.json").write_text("{", encoding="utf-8")

    recorded = maybe_record_observation(
        store,
        technique="verdict",
        base_rev="base-pin",
        head_rev="head-pin",
        result="pass",
    )

    assert recorded is False
    assert "malformed JSON in config.json" in capsys.readouterr().err
