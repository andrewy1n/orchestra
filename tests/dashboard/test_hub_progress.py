from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fastapi")
from conftest import REPO_ROOT
from fastapi.testclient import TestClient

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.hub import WORK_NEXT_LIMIT, HubItem, build_hub
from dashboard.backend.landing import Landing
from dashboard.backend.phase import PhaseEvidence, PhaseRow
from dashboard.backend.progress import Progress
from dashboard.backend.server.app import create_app
from dashboard.backend.snapshot import BacklogItem, EffortView, NeedsYouItem, Snapshot
from dashboard.backend.task import TaskRow
from orchestra.canon.project import open_store

NOW = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
MERGED = Landing(branch="phase/x", exists=True, ahead=0, merged=True)


def _phase(
    subject: str,
    *,
    state: str = "in_progress",
    running: bool = False,
    age: timedelta = timedelta(hours=2),
    done: int = 1,
    total: int = 2,
) -> PhaseRow:
    return PhaseRow(
        subject=subject,
        title=f"Title {subject}",
        ordinal=1,
        state=state,
        done=done,
        total=total,
        evidence=PhaseEvidence(
            phase=subject,
            weight="full",
            requirements=(),
            stage="execute",
            integration=None,
            release_ready=False,
            decisions=(),
            non_goals="",
        ),
        in_progress=("t",) if running else (),
        updated_at=NOW - age,
    )


def _task(phase: str, name: str, status: str) -> TaskRow:
    return TaskRow(
        id=f"id-{phase}-{name}",
        subject=name,
        title=name,
        phase=phase,
        assignee="",
        wave=1,
        status=status,
    )


def _effort(
    name: str,
    phases: list[PhaseRow],
    *,
    dormant: bool = False,
    needs: int = 0,
    ideas: int = 0,
) -> EffortView:
    tasks = [_task(p.subject, n, s) for p in phases for n, s in (("a", "done"), ("b", "planned"))]
    return EffortView(
        effort=name,
        goal="",
        phases=phases,
        tasks=tasks,
        needs_you=[
            NeedsYouItem(
                kind="open-question",
                id=f"{name}-n{i}",
                subject=f"{name}-n{i}",
                text=f"Q{i}",
                status="open",
                updated_at=NOW - timedelta(days=1, minutes=i),
            )
            for i in range(needs)
        ],
        backlog=[
            BacklogItem(
                id=f"{name}-i{i}",
                subject=f"{name}-i{i}",
                effort=name,
                text=f"Idea {i}",
                status="open",
                updated_at=NOW - timedelta(days=2, minutes=i),
            )
            for i in range(ideas)
        ],
        dormant=dormant,
    )


def _snapshot(*efforts: EffortView) -> Snapshot:
    return Snapshot(efforts=list(efforts), token="t", generated_at=NOW)


def _hub(snap: Snapshot, **extra):
    return build_hub(
        snap,
        NOW,
        landings=extra.pop("landings", {}),
        approvals=extra.pop("approvals", {}),
        review_passed=extra.pop("review_passed", frozenset()),
    )


def _subjects(items: list[HubItem]) -> list[str]:
    return [item.subject for item in items]


def test_r2_one_card_per_in_progress_phase_of_each_active_effort() -> None:
    snap = _snapshot(
        _effort("alpha", [_phase("a1"), _phase("a2"), _phase("a3", state="planned")]),
        _effort("beta", [_phase("b1"), _phase("b2", state="done")]),
        _effort("old", [_phase("o1", state="done")]),
        _effort("sleepy", [_phase("s1")], dormant=True),
    )
    hub = _hub(snap)
    assert sorted(_subjects(hub.active_phases)) == ["a1", "a2", "b1"]


def test_r2_each_card_carries_a_progress_object() -> None:
    snap = _snapshot(_effort("alpha", [_phase("a1")]), _effort("beta", [_phase("b1")]))
    hub = _hub(
        snap,
        landings={"a1": MERGED},
        approvals={"a1": {"spec", "design", "plan"}},
        review_passed=frozenset({"a1"}),
    )
    assert len(hub.active_phases) == 2
    for card in hub.active_phases:
        progress = card.progress
        assert isinstance(progress, Progress)
        assert progress.weight == "full"
        assert progress.stages[0].id == "spec"
        assert progress.tasks.done == 1
        assert progress.tasks.total == 2
        assert hasattr(progress, "requirements")
        assert hasattr(progress, "repairs")
        assert progress.blockers.text
    by_subject = {
        card.subject: card.progress for card in hub.active_phases if card.progress is not None
    }
    spec_state = {s.id: s.state for s in by_subject["a1"].stages}
    assert spec_state["spec"] == "done"
    assert spec_state["review"] == "done"
    assert spec_state["land"] == "done"
    assert {s.id: s.state for s in by_subject["b1"].stages}["spec"] == "current"


def test_r2_needs_and_ideas_carry_no_progress() -> None:
    hub = _hub(_snapshot(_effort("alpha", [_phase("a1")], needs=1, ideas=1)))
    assert hub.needs_you and hub.open_ideas
    assert all(item.progress is None for item in [*hub.needs_you, *hub.open_ideas])


def test_r2_no_card_for_finished_dormant_or_not_in_progress() -> None:
    snap = _snapshot(
        _effort("old", [_phase("o1", state="done")]),
        _effort("sleepy", [_phase("s1")], dormant=True),
        _effort("alpha", [_phase("a1", state="planned")]),
    )
    assert _hub(snap).active_phases == []


def test_r3_running_phase_first_then_most_recent_write() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            [
                _phase("old", age=timedelta(days=4)),
                _phase("new", age=timedelta(minutes=10)),
                _phase("busy", running=True, age=timedelta(days=9)),
            ],
        ),
        _effort("beta", [_phase("mid", age=timedelta(hours=3))]),
    )
    assert _subjects(_hub(snap).active_phases) == ["busy", "new", "mid", "old"]


def test_r3_ties_are_stable_by_effort_then_subject() -> None:
    same = timedelta(hours=1)
    snap = _snapshot(
        _effort("beta", [_phase("b", age=same)]),
        _effort("alpha", [_phase("z", age=same), _phase("a", age=same)]),
    )
    first = [(c.effort, c.subject) for c in _hub(snap).active_phases]
    second = [(c.effort, c.subject) for c in _hub(snap).active_phases]
    assert first == second == [("alpha", "a"), ("alpha", "z"), ("beta", "b")]


def test_r13_work_next_excludes_every_phase_with_a_card() -> None:
    snap = _snapshot(
        _effort("alpha", [_phase("a1"), _phase("a2", running=True)], needs=2, ideas=2),
        _effort("beta", [_phase("b1")], needs=1),
    )
    hub = _hub(snap)
    card_slugs = set(_subjects(hub.active_phases))
    assert card_slugs == {"a1", "a2", "b1"}
    assert not card_slugs & set(_subjects(hub.work_next))
    assert all(item.kind != "phase" for item in hub.work_next)


def test_r13_work_next_still_fills_its_limit_after_filtering() -> None:
    phases = [_phase(f"p{i}", age=timedelta(minutes=i + 1)) for i in range(4)]
    snap = _snapshot(_effort("alpha", phases, needs=4, ideas=4))
    hub = _hub(snap)
    assert len(hub.work_next) == WORK_NEXT_LIMIT
    assert {item.kind for item in hub.work_next} <= {"needs", "idea"}
    assert not {f"p{i}" for i in range(4)} & set(_subjects(hub.work_next))


def test_r2_hub_endpoint_serialises_the_progress_object(store, cli) -> None:
    def create(kind: str, subject: str, payload: dict, body: str) -> None:
        result = cli(
            "create", "--type", kind, "--subject", subject,
            "--payload", json.dumps(payload), "--body", body,
        )  # fmt: skip
        assert result.returncode == 0, result.stdout + result.stderr

    create("score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"}, "g\n")
    create(
        "score:phase",
        "card-phase",
        {"title": "Card phase", "ordinal": 1, "effort": "alpha"},
        "## Problem\n\nT.\n\n## Approach\n\nT.\n\n## Exit criteria\n\nT.\n",
    )
    result = cli("update", "--type", "score:phase", "--subject", "card-phase",
                 "--transition", "in_progress")  # fmt: skip
    assert result.returncode == 0, result.stdout + result.stderr
    create(
        "score:work-item",
        "task-one",
        {"title": "t", "phase": "card-phase", "kind": "deliver", "assignee": "",
         "effort": "alpha", "attempts": 0, "estimate_minutes": 0},
        "## Description\n\nT.\n",
    )  # fmt: skip

    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/api/hub")
    assert response.status_code == 200, response.text
    body = response.json()
    cards = [c for c in body["active_phases"] if c["subject"] == "card-phase"]
    assert len(cards) == 1, body
    progress = cards[0]["progress"]
    assert set(progress) >= {"weight", "stages", "tasks", "requirements", "repairs", "blockers"}
    assert progress["tasks"]["total"] == 1
    assert {"id", "state"} <= set(progress["stages"][0])
    assert {"shown", "more", "text"} <= set(progress["blockers"])
    assert "card-phase" not in [i["subject"] for i in body["work_next"]]
