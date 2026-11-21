from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import current_placements, home_area, read_idea


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
