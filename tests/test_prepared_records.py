from __future__ import annotations

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.acceptance_amendment import COMMAND_AMENDMENT_KEY
from orchestra.conductor.head_evidence import EvidenceIndex
from orchestra.score.lookups import cached_object, prepare_records


def _bare(
    record_id: str,
    record_type: str,
    subject: str,
    payload: JsonObject,
    provenance: JsonObject | None = None,
) -> Record:
    record: Record = {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "r",
        "recorded_at": "2026-01-01T00:00:00Z",
        "body": "",
    }
    if provenance is not None:
        record["provenance"] = provenance
    return record


def test_subset_index_does_not_reuse_the_prepared_catalog() -> None:
    check = _bare(
        "check-1",
        "tuner:check-run",
        "p-suite",
        {"criterion_id": "p-suite", "evidence_kind": "integration", "result": "pass"},
    )
    amendment = _bare(
        "amend-1",
        "conductor:assignment-amendment",
        "amend",
        {},
        provenance={COMMAND_AMENDMENT_KEY: "acc-1"},
    )
    acceptance = _bare("acc-1", "score:acceptance", "acc", {})
    full = [check, amendment]
    with prepare_records(full):
        assert EvidenceIndex([check]).command_was_amended(acceptance) is False
        assert EvidenceIndex(full).command_was_amended(acceptance) is True


def test_wrong_evidence_cache_type_raises() -> None:
    check = _bare("check-1", "tuner:check-run", "p-suite", {"result": "pass"})
    with prepare_records([check]):
        cached_object([check], "evidence-index", lambda: object())
        with pytest.raises(TypeError, match="evidence-index"):
            EvidenceIndex([check])
