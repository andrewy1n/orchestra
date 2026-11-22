from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import current_placements, home_area, open_ideas, read_idea


def _record(record_type: str, subject: str, payload: JsonObject, rid: str, at: str) -> Record:
    return {
        "id": rid,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r",
        "recorded_at": at,
    }


def _placement(effort: str, area: str, rid: str, at: str) -> Record:
    return _record("composer:placement", effort, {"area": area}, rid, at)


def _idea(payload: JsonObject, rid: str = "i1") -> Record:
    return _record("composer:idea", "an-idea", payload, rid, "2026-01-01T00:00:00Z")


def test_promoted_idea_takes_its_placement_area():
    placements = current_placements(
        [
            _placement("e1", "old-area", "p1", "2026-01-01T00:00:00Z"),
            _placement("e1", "new-area", "p2", "2026-01-02T00:00:00Z"),
        ]
    )
    idea = read_idea(_idea({"status": "promoted", "effort": "e1", "area": "own-area"}))
    assert home_area(idea, placements) == "new-area"


def test_unpromoted_idea_keeps_its_own_area():
    placements = {"e1": "placed-area"}
    open_idea = read_idea(_idea({"status": "open", "effort": "e1", "area": "own-area"}))
    unplaced = read_idea(_idea({"status": "promoted", "effort": "e2", "area": "own-area"}))
    bare = read_idea(_idea({"status": "open"}))
    assert home_area(open_idea, placements) == "own-area"
    assert home_area(unplaced, placements) == "own-area"
    assert home_area(bare, placements) == ""


def _listed(subject: str, status: str, rid: str, state: str = "active") -> Record:
    record = _record("composer:idea", subject, {"status": status}, rid, "2026-01-01T00:00:00Z")
    record["lifecycle_state"] = state
    return record


def test_open_ideas_keep_only_live_open_ideas() -> None:
    records = [
        _listed("open-one", "open", "i1"),
        _listed("promoted-one", "promoted", "i2"),
        _listed("dismissed-one", "dismissed", "i3"),
        _listed("old-one", "open", "i4", state="superseded"),
        _listed("gone-one", "open", "i5", state="retracted"),
    ]
    assert [idea.subject for idea in open_ideas(records)] == ["open-one"]


def test_open_ideas_sort_by_subject_then_record_id() -> None:
    records = [
        _listed("zeta", "open", "i1"),
        _listed("alpha", "open", "i9"),
        _listed("alpha", "open", "i2"),
    ]
    assert [(idea.subject, idea.record["id"]) for idea in open_ideas(records)] == [
        ("alpha", "i2"),
        ("alpha", "i9"),
        ("zeta", "i1"),
    ]
