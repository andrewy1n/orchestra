from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.placement import PlacementError, place
from orchestra.score.planning import autonomy
from orchestra.score.planning.effort import current_efforts

GRANT = "Plan-review gates are preauthorized by the user."


@dataclass(frozen=True)
class _StaleProject(Project):
    """A project whose records of one subject read as superseded, as a stale lookup would see them."""

    dead_type: str = ""
    dead_subject: str = ""

    def _dead(self, record: Record) -> Record:
        if record["record_type"] == self.dead_type and record["subject"] == self.dead_subject:
            return {**record, "lifecycle_state": "superseded"}
        return record

    def records(self) -> list[Record]:
        return [self._dead(record) for record in super().records()]

    def list(self, record_type: str) -> list[Record]:
        return [self._dead(record) for record in super().list(record_type)]

    def resolve(self, record_type: str, subject: str) -> Record:
        return self._dead(super().resolve(record_type, subject))


def _stale(project: Project, record_type: str, subject: str) -> Project:
    return _StaleProject(
        project.project_root,
        project.store_path,
        project.binding,
        project.read_only,
        record_type,
        subject,
    )


def _record(record_type: str, subject: str, payload: JsonObject) -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00+00:00",
    }


def _effort_records(*subjects: str) -> list[Record]:
    return [_record("score:effort", s, {"goal": "g", "kind": "deliver"}) for s in subjects]


def test_place_fails_for_unknown_effort_or_area(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "alpha", {"goal": "g", "kind": "deliver"})
    create(project, "composer:area", "billing", {"title": "Billing"})
    with pytest.raises(PlacementError, match="ghost"):
        place(project, "ghost", "billing")
    with pytest.raises(PlacementError, match="nowhere"):
        place(project, "alpha", "nowhere")
    with pytest.raises(PlacementError, match="alpha"):
        place(_stale(project, "score:effort", "alpha"), "alpha", "billing")
    with pytest.raises(PlacementError, match="billing"):
        place(_stale(project, "composer:area", "billing"), "alpha", "billing")
    assert project.list("composer:placement") == []


def test_record_belongs_to_effort_only_through_its_field() -> None:
    known = current_efforts(_effort_records("alpha", "dashboard-features"))
    by_field = _record("score:phase", "p1", {"effort": "alpha"})
    by_applies_to = _record("score:constraint", "c1", {"applies_to": "alpha"})
    suffixed = _record("score:constraint", "dashboard-autonomy-dashboard-features", {})
    own_subject = _record("score:constraint", "alpha", {})
    retired = _record("score:constraint", "c2", {"applies_to": "gone", "effort": "gone"})
    applies_on_phase = _record("score:phase", "p2", {"applies_to": "alpha"})
    assert autonomy.resolve_effort(by_field, known) == "alpha"
    assert autonomy.resolve_effort(by_applies_to, known) == "alpha"
    assert autonomy.resolve_effort(suffixed, known) == ""
    assert autonomy.resolve_effort(own_subject, known) == ""
    assert autonomy.resolve_effort(retired, known) == ""
    assert autonomy.resolve_effort(applies_on_phase, known) == ""


def test_autonomy_migration_leaves_unmatched_constraint_with_a_note(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "alpha", {"goal": "g", "kind": "deliver"})
    create(project, "score:effort", "other", {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:constraint",
        "gates-other",
        {"statement": GRANT, "applies_to": "alpha", "effort": "alpha"},
    )
    mappings, notes = autonomy.plan_migration(_stale(project, "score:effort", "alpha"))
    assert mappings == []
    assert notes == ["gates-other: grants autonomy but covers no known effort; left alone"]
    constraint = project.resolve("score:constraint", "gates-other")
    assert constraint["lifecycle_state"] == "active"
    assert constraint["payload"]["statement"] == GRANT
