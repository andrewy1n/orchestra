from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.score.planning.phase import Phase, current_phase_model, read_phase
from orchestra.score.planning.requirements import requirement_body_problems, requirements_in_body
from orchestra.score.workflow.workflow_reviews import (
    light_phase_fingerprints,
    step_input_fingerprint,
)

BODIES = {
    "plain": (
        "## Problem\nP one.\n\n## Requirements\n\nR1: first\nR2: second\n\n"
        "## Non-goals\nNone.\n\n## Approach\nA.\n\n## Exit criteria\nE.\n"
    ),
    "trailing-whitespace": (
        "## Problem\nline with trailing   \nsecond\t\n\n## Approach\nA.  \n\n## Proof\nP.\n"
    ),
    "duplicate-heading": (
        "## Problem\nfirst\n\n## Approach\nA.\n\n## Problem\nsecond\n\n## Proof\nP.\n"
    ),
    "spaced-heading": "##  Problem\nP.\n\n## Approach   \nA.\n\n## Exit criteria\nE.\n",
    "crlf": "## Problem\r\nP.\r\n\r\n## Approach\r\nA.\r\n\r\n## Exit criteria\r\nE.\r\n",
    "preamble-and-subheading": (
        "Intro text.\n\n## Problem\nP.\n### Sub\nx\n## Approach\nA.\n## Exit criteria\nE.\n"
    ),
    "code-fence": "## Problem\nP.\n```\n## Approach\n```\n## Approach\nreal\n## Proof\nP.\n",
}

FINGERPRINTS = {
    "plain": (
        "aa115a37becb5ccd772a1370144e1d2bde0bafbd07b12e5d75cc2849148f836e",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "5d4f22325336b75a708f9663d0ae2c9e3bce6c0df1e4c98d4427199e5c498c5d",
    ),
    "trailing-whitespace": (
        "1cf0cfd10a455cd264d63c742bf9e54cb46b78cbe7f9fcd8967682f1df1394e0",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "6de39039341ccb0bc37b0a158860a017b749f30bda180169fea227da0834bedf",
    ),
    "duplicate-heading": (
        "e7ddbbdde07543338d1ac3a7472388f6392baa56db34b755f113cb46625127bf",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "6de39039341ccb0bc37b0a158860a017b749f30bda180169fea227da0834bedf",
    ),
    "spaced-heading": (
        "a90a8fa6a5edba9a2da17d06f01a9b35cc9c9b2e7e50b8518a94c540ccf5b264",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "5d4f22325336b75a708f9663d0ae2c9e3bce6c0df1e4c98d4427199e5c498c5d",
    ),
    "crlf": (
        "a90a8fa6a5edba9a2da17d06f01a9b35cc9c9b2e7e50b8518a94c540ccf5b264",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "5d4f22325336b75a708f9663d0ae2c9e3bce6c0df1e4c98d4427199e5c498c5d",
    ),
    "preamble-and-subheading": (
        "49ffdf192e6298c0003fc2a5d521b2fd490fd516d6fc94cb5638f1776d87d12b",
        "bddefeae7485155993748e75896b32a4033a611cf37e02a226877830a98d025d",
        "5d4f22325336b75a708f9663d0ae2c9e3bce6c0df1e4c98d4427199e5c498c5d",
    ),
    "code-fence": (
        "b2541e3f8249441600ecf0bdf5d9649e8746eb35daea4b74e1fc6450c53b988d",
        "3d4c84311fae6b3b6947e78788148b32ec5e01b9aa28bef05c12ae74f1934919",
        "6de39039341ccb0bc37b0a158860a017b749f30bda180169fea227da0834bedf",
    ),
}


def _phase_record(
    *,
    record_id: str = "rec-1",
    subject: str = "feature",
    payload: JsonObject | None = None,
    body: str | None = None,
    lifecycle_state: str = "active",
    recorded_at: str = "2026-01-01T00:00:00Z",
    corrects: list[str] | None = None,
) -> Record:
    record: Record = {
        "id": record_id,
        "record_type": "score:phase",
        "subject": subject,
        "payload": {"title": "Feature", "ordinal": 3, "effort": "workflow"}
        if payload is None
        else payload,
        "lifecycle_state": lifecycle_state,
        "relationships": {"corrects": corrects} if corrects else {},
        "revision": "rev-1",
        "recorded_at": recorded_at,
    }
    if body is not None:
        record["body"] = body
    return record


@pytest.mark.parametrize("name", sorted(BODIES))
def test_r12_light_phase_fingerprints_keep_their_recorded_digests(name: str) -> None:
    fingerprints = light_phase_fingerprints(BODIES[name])

    assert (
        fingerprints.contract,
        fingerprints.approach,
        fingerprints.proof,
    ) == FINGERPRINTS[name]


def test_r12_step_input_fingerprint_of_light_phase_keeps_its_recorded_digest() -> None:
    phase = _phase_record(
        payload={"title": "Feature", "ordinal": 1, "effort": "workflow", "weight": "light"},
        body=BODIES["plain"],
    )

    assert step_input_fingerprint("design", phase, [], [phase]) == (
        "db8e61427c10d7a1f235b6295065ea640c835b497ed1e2d1f2ecae30f26dc966"
    )


def test_r12_requirement_parsing_keeps_its_recorded_output() -> None:
    assert requirements_in_body(BODIES["plain"]) == [("R1", "first"), ("R2", "second")]
    assert requirement_body_problems(BODIES["plain"]) == []
    assert requirement_body_problems(BODIES["duplicate-heading"]) == [
        "the body has no ## Requirements section"
    ]


def test_r12_read_phase_keeps_the_stored_record_and_raw_body() -> None:
    record = _phase_record(
        payload={
            "title": "Feature",
            "ordinal": 3,
            "effort": "workflow",
            "milestone": "m1",
            "weight": "light",
            "oracle_policy": "frozen",
        },
        body=BODIES["plain"],
    )

    phase = read_phase(record)

    assert phase == Phase(
        id="rec-1",
        subject="feature",
        title="Feature",
        ordinal=3,
        effort="workflow",
        milestone="m1",
        weight="light",
        oracle_policy="frozen",
        body=BODIES["plain"],
        record=record,
    )
    assert phase.record is record


def test_r12_read_phase_leaves_absent_optional_fields_none() -> None:
    phase = read_phase(_phase_record())

    assert (phase.milestone, phase.weight, phase.oracle_policy, phase.body) == (
        None,
        None,
        None,
        "",
    )
    assert (phase.title, phase.ordinal, phase.effort) == ("Feature", 3, "workflow")


@pytest.mark.parametrize("field", ["title", "ordinal", "effort"])
def test_r12_read_phase_rejects_missing_required_field(field: str) -> None:
    payload: JsonObject = {"title": "Feature", "ordinal": 3, "effort": "workflow"}
    del payload[field]

    with pytest.raises(RecordShapeError) as caught:
        read_phase(_phase_record(payload=payload))

    assert (caught.value.record_id, caught.value.field) == ("rec-1", field)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", 5),
        ("ordinal", "3"),
        ("ordinal", True),
        ("ordinal", 1.5),
        ("effort", None),
        ("milestone", 7),
        ("weight", 1),
        ("weight", "heavy"),
        ("oracle_policy", ["none"]),
        ("oracle_policy", "strict"),
    ],
)
def test_r12_read_phase_rejects_wrong_typed_field(field: str, value: object) -> None:
    payload: JsonObject = {"title": "Feature", "ordinal": 3, "effort": "workflow"}
    payload[field] = value  # pyright: ignore[reportArgumentType] -- deliberately malformed
    with pytest.raises(RecordShapeError) as caught:
        read_phase(_phase_record(payload=payload))

    assert (caught.value.record_id, caught.value.field) == ("rec-1", field)


def test_r12_read_phase_rejects_non_string_body() -> None:
    record = _phase_record()
    record["body"] = 5  # pyright: ignore[reportGeneralTypeIssues] -- deliberately malformed

    with pytest.raises(RecordShapeError) as caught:
        read_phase(record)

    assert caught.value.field == "body"


def test_r12_current_phase_model_follows_the_current_phase_selection() -> None:
    old = _phase_record(record_id="rec-1", recorded_at="2026-01-01T00:00:00Z")
    newest = _phase_record(
        record_id="rec-2",
        recorded_at="2026-01-02T00:00:00Z",
        payload={"title": "Newer", "ordinal": 4, "effort": "workflow"},
    )
    superseded = _phase_record(
        record_id="rec-3", recorded_at="2026-01-03T00:00:00Z", lifecycle_state="superseded"
    )
    corrected_away = _phase_record(
        record_id="rec-4", recorded_at="2026-01-04T00:00:00Z", corrects=["rec-9"]
    )
    corrector = _phase_record(
        record_id="rec-9",
        subject="other",
        recorded_at="2026-01-05T00:00:00Z",
        corrects=["rec-4"],
    )

    phase = current_phase_model("feature", [old, newest, superseded, corrected_away, corrector])

    assert phase is not None
    assert (phase.id, phase.title, phase.ordinal) == ("rec-2", "Newer", 4)
    assert phase.record is newest


def test_r12_current_phase_model_is_none_without_a_current_phase() -> None:
    superseded = _phase_record(lifecycle_state="superseded")

    assert current_phase_model("feature", [superseded]) is None
    assert current_phase_model("missing", [_phase_record()]) is None
