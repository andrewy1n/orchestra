"""Each running phase keeps its own position; handoff groups every record under its effort."""

from __future__ import annotations

import json

from canon.project import open_store

import helpers as h
from orchestra import views

EFFORT = "area"


def _phase_position(cli, defs, phase: str) -> dict:
    h.create_generic_record(
        cli, defs, "plan:phase", subject=phase,
        extra_payload={"title": f"title of {phase}", "ordinal": 1, "effort": EFFORT},
    )
    return h.create_generic_record(
        cli, defs, "plan:position", subject=phase,
        extra_payload={"position": f"working on {phase}", "scope": "phase", "effort": EFFORT, "phase": phase},
    )


def _handoff(store) -> str:
    return views.render_view(views.VIEWS["handoff"], views.load_records(open_store(store)))


def _effort_section(handoff: str) -> str:
    start = handoff.index(f"## {EFFORT}\n")
    end = handoff.find("\n## ", start + 1)
    return handoff[start:] if end == -1 else handoff[start:end]


def test_two_phases_of_one_effort_keep_separate_positions_under_the_effort(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    h.create_generic_record(
        cli, defs, "plan:effort", subject=EFFORT,
        extra_payload={"goal": "ship the area", "kind": "deliver"},
    )
    _phase_position(cli, defs, "area-one")
    _phase_position(cli, defs, "area-two")

    assert cli("validate").returncode == 0
    handoff = _handoff(store)
    section = _effort_section(handoff)
    assert "working on area-one" in section and "working on area-two" in section
    assert "## area-one" not in handoff and "## area-two" not in handoff


def test_closing_a_phase_position_hides_only_that_phase(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    first = _phase_position(cli, defs, "area-one")
    _phase_position(cli, defs, "area-two")
    result = cli(
        "supersede", "--type", "plan:position", "--id", first["id"],
        "--expected-revision", first["revision"], "--payload", json.dumps({"status": "closed"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    section = _effort_section(_handoff(store))
    assert "working on area-one" not in section and "working on area-two" in section


def test_work_item_renders_under_its_effort_not_its_task_slug(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    phase = h.create_generic_record(
        cli, defs, "plan:phase", subject="area-one",
        extra_payload={"title": "first", "ordinal": 1, "effort": EFFORT},
    )
    task = h.create_generic_record(
        cli, defs, "plan:work-item", subject="some-task",
        extra_payload={"title": "a task", "phase": phase["subject"], "effort": EFFORT, "kind": "deliver"},
    )
    h.transition(cli, "plan:work-item", task, "in_progress")

    handoff = _handoff(store)
    assert "**some-task**" in _effort_section(handoff)
    assert "## some-task" not in handoff
