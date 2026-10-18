"""Milestone grouping in the dashboard model and task sections."""

from __future__ import annotations

import sys

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from dashboard import model  # noqa: E402
from dashboard import selection  # noqa: E402
from dashboard import tasks  # noqa: E402
from dashboard.display import ANSI_PALETTE  # noqa: E402


def phase(
    subject: str, state: str, ordinal: int, *, milestone: str = "", milestone_title: str = "",
    done: int = 0, total: int = 1,
) -> model.PhaseRow:
    return model.PhaseRow(
        subject=subject, title=subject, ordinal=ordinal, state=state, done=done, total=total,
        milestone=milestone, milestone_title=milestone_title,
    )


def milestone(subject: str, title: str, ordinal: int, *, done: int = 0, total: int = 0, state: str = "planned") -> model.MilestoneRow:
    return model.MilestoneRow(subject=subject, title=title, ordinal=ordinal, state=state, done=done, total=total)


def test_attach_milestones_titles_and_sorts_ungrouped_first():
    phases = [
        phase("b", "planned", 2, milestone="cutover"),
        phase("a", "planned", 1, milestone="harden"),
        phase("solo", "in_progress", 3),
    ]
    rows = [
        milestone("harden", "Harden", 2),
        milestone("cutover", "Cutover", 1),
    ]
    attached = model.attach_milestones(phases, rows)
    assert [row.subject for row in attached] == ["solo", "b", "a"]
    assert attached[1].milestone_title == "Cutover"
    assert attached[2].milestone_title == "Harden"
    assert attached[0].milestone_title == ""


def test_milestone_rows_derive_state_and_counts():
    phases = [
        phase("p1", "done", 1, milestone="cutover"),
        phase("p2", "in_progress", 2, milestone="cutover"),
        phase("p3", "planned", 3, milestone="harden"),
    ]
    records = [
        {
            "id": "m1", "subject": "cutover", "lifecycle_state": "planned",
            "payload": {"title": "Cutover", "ordinal": 1, "effort": "e"},
        },
        {
            "id": "m2", "subject": "harden", "lifecycle_state": "planned",
            "payload": {"title": "Harden", "ordinal": 2, "effort": "e"},
        },
    ]
    rows = model._milestone_rows(records, phases)
    assert [(row.subject, row.state, row.done, row.total) for row in rows] == [
        ("cutover", "in_progress", 1, 2),
        ("harden", "planned", 0, 1),
    ]


def test_section_rows_insert_milestone_headers():
    phases = [
        phase("solo", "in_progress", 1),
        phase("dual", "planned", 2, milestone="cutover", milestone_title="Cutover"),
    ]
    milestones = [milestone("cutover", "Cutover", 1, done=0, total=1)]
    view = model.EffortView(
        "e", "g",
        phases=phases,
        milestones=milestones,
        tasks=[
            model.TaskRow(id="t1", subject="t1", title="t1", phase="solo", assignee="", wave=1, status="running"),
            model.TaskRow(id="t2", subject="t2", title="t2", phase="dual", assignee="", wave=1, status="ready"),
        ],
    )
    sections = tasks.section_rows(view, view.tasks, {"phase:solo": True, "phase:dual": True}, show_empty=False)
    assert [(row.kind, row.key, row.milestone_title) for row in sections if row.kind != "task"] == [
        ("milestone", tasks.UNGROUPED_KEY, "Ungrouped"),
        ("phase", "phase:solo", ""),
        ("milestone", "milestone:cutover", "Cutover"),
        ("phase", "phase:dual", ""),
    ]


def test_section_rows_skip_headers_when_no_milestones():
    view = model.EffortView(
        "e", "g",
        phases=[phase("p1", "in_progress", 1)],
        tasks=[model.TaskRow(id="t1", subject="t1", title="t1", phase="p1", assignee="", wave=1, status="running")],
    )
    sections = tasks.section_rows(view, view.tasks, {"phase:p1": True}, show_empty=False)
    assert [row.kind for row in sections] == ["phase", "task"]


def test_selector_shows_milestone_on_selected_phase():
    view = model.EffortView(
        "e", "g",
        phases=[phase("p1", "in_progress", 1, milestone="cutover", milestone_title="Cutover", done=0, total=1)],
    )
    segments = selection.selector_segments(view, "p1", ANSI_PALETTE)
    assert any("Cutover" in segment.plain for segment in segments)
