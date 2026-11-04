"""Oracles for promoted ideas whose effort placement holds no area."""

from __future__ import annotations

from dashboard.backend.areas import _home_area
from orchestra.canon.types import Record


def _idea(status: str, **refs: str) -> Record:
    return {
        "id": "rec-idea",
        "record_type": "composer:idea",
        "subject": "refund-flow",
        "payload": {"status": status, **refs},
        "lifecycle_state": "current",
        "relationships": {},
        "revision": "sha256:test",
        "recorded_at": "2026-01-01T00:00:00+00:00",
    }


def test_r14_promoted_idea_falls_back_to_its_own_area_when_the_placement_area_is_empty():
    idea = _idea("promoted", effort="alpha", area="billing")
    assert _home_area(idea, {"alpha": ""}) == "billing"


def test_r14_promoted_idea_uses_the_placement_area_when_it_is_set():
    idea = _idea("promoted", effort="alpha", area="billing")
    assert _home_area(idea, {"alpha": "search"}) == "search"


def test_r14_promoted_idea_with_an_empty_placement_and_no_own_area_has_no_home():
    idea = _idea("promoted", effort="alpha")
    assert _home_area(idea, {"alpha": ""}) == ""


def test_r14_open_idea_keeps_its_own_area_whatever_the_placement_holds():
    idea = _idea("open", effort="alpha", area="billing")
    assert _home_area(idea, {"alpha": "search"}) == "billing"
