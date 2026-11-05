from __future__ import annotations

from pathlib import Path

import pytest

from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.canon.validation import ValidationError
from orchestra.tuner.binding import BindingError, bind_observation
from orchestra.tuner.observation import maybe_record_observation, record_observation


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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CANON_STORE", str(tmp_path / "missing"))

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
