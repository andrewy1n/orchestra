from __future__ import annotations

import itertools
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import REPO_ROOT
from test_review_stage import EFFORT, _project_with_phases, _review_run, _review_state

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.hub import HubItem, HubView, build_hub
from dashboard.backend.phase import PhaseEvidence, PhaseRow
from dashboard.backend.server import service
from dashboard.backend.snapshot import BacklogItem, EffortView, NeedsYouItem, Snapshot
from orchestra.canon import record as record_module
from orchestra.canon.project import Project

NOW = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


def _ago(**delta: float) -> datetime:
    return NOW - timedelta(**delta)


def _evidence(phase: str, stage: str) -> PhaseEvidence:
    return PhaseEvidence(
        phase=phase,
        weight="full",
        requirements=(),
        stage=stage,
        integration=None,
        release_ready=False,
        decisions=(),
        non_goals="",
    )


def _phase(
    subject: str,
    *,
    state: str = "in_progress",
    running: bool = False,
    age: timedelta = timedelta(hours=2),
    stage: str = "execute",
) -> PhaseRow:
    return PhaseRow(
        subject=subject,
        title=f"Title {subject}",
        ordinal=1,
        state=state,
        done=0,
        total=1,
        evidence=_evidence(subject, stage),
        in_progress=("task-a",) if running else (),
        updated_at=NOW - age,
    )


def _need(
    item_id: str, *, status: str = "open", age: timedelta = timedelta(hours=2)
) -> NeedsYouItem:
    return NeedsYouItem(
        kind="open-question",
        id=item_id,
        subject=item_id,
        text=f"Question {item_id}",
        status=status,
        updated_at=NOW - age,
    )


def _idea(item_id: str, *, status: str = "open", age: timedelta = timedelta(days=3)) -> BacklogItem:
    return BacklogItem(
        id=item_id,
        subject=item_id,
        effort="alpha",
        text=f"Idea {item_id}",
        status=status,
        updated_at=NOW - age,
    )


def _effort(
    name: str,
    *,
    phases: list[PhaseRow] | None = None,
    needs: list[NeedsYouItem] | None = None,
    ideas: list[BacklogItem] | None = None,
    dormant: bool = False,
) -> EffortView:
    return EffortView(
        effort=name,
        goal="",
        phases=phases or [],
        needs_you=needs or [],
        backlog=ideas or [],
        dormant=dormant,
    )


def _snapshot(*efforts: EffortView) -> Snapshot:
    return Snapshot(efforts=list(efforts), token="t", generated_at=NOW)


def _subjects(items: list[HubItem]) -> list[str]:
    return [item.subject for item in items]


def test_r2_lists_active_phases_across_live_efforts_with_step() -> None:
    snap = _snapshot(
        _effort("alpha", phases=[_phase("p1", stage="execute"), _phase("p2", state="planned")]),
        _effort("beta", phases=[_phase("p3", stage="verify"), _phase("p4", state="done")]),
        _effort("gamma", phases=[_phase("p5")], dormant=True),
    )
    hub = build_hub(snap, NOW)
    assert isinstance(hub, HubView)
    assert sorted(_subjects(hub.active_phases)) == ["p1", "p3"]
    by_subject = {item.subject: item for item in hub.active_phases}
    assert by_subject["p1"].effort == "alpha"
    assert by_subject["p1"].title == "Title p1"
    assert by_subject["p1"].step == "execute"
    assert by_subject["p3"].step == "verify"
    assert by_subject["p1"].href == "#/phase/alpha/p1"


def test_r3_lists_only_open_needs_you_items() -> None:
    snap = _snapshot(
        _effort("alpha", needs=[_need("n1"), _need("n2", status="settled")]),
        _effort("beta", needs=[_need("n3")]),
    )
    hub = build_hub(snap, NOW)
    assert sorted(_subjects(hub.needs_you)) == ["n1", "n3"]
    assert {item.href for item in hub.needs_you} == {"#/needs/alpha/n1", "#/needs/beta/n3"}


def test_r4_lists_only_open_ideas() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            ideas=[
                _idea("i1"),
                _idea("i2", status="promoted"),
                _idea("i3", status="dismissed"),
            ],
        )
    )
    hub = build_hub(snap, NOW)
    assert _subjects(hub.open_ideas) == ["i1"]
    assert [item.href for item in hub.open_ideas] == ["#/backlog/alpha/i1"]


def test_r5_work_next_holds_at_most_five_and_is_deterministic() -> None:
    phases = [_phase(f"p{i}", age=timedelta(hours=i + 1)) for i in range(4)]
    needs = [_need(f"n{i}", age=timedelta(hours=10 + i)) for i in range(3)]
    ideas = [_idea(f"i{i}", age=timedelta(days=2 + i)) for i in range(3)]
    snap = _snapshot(_effort("alpha", phases=phases, needs=needs, ideas=ideas))
    first = build_hub(snap, NOW)
    second = build_hub(snap, NOW)
    assert len(first.work_next) == 5
    assert _subjects(first.work_next) == _subjects(second.work_next)
    kinds = {item.kind for item in first.work_next}
    assert len(kinds) > 1


def test_r5_equal_recency_ties_break_by_effort_then_subject() -> None:
    same = timedelta(hours=1)
    snap = _snapshot(
        _effort("beta", phases=[_phase("b", age=same)]),
        _effort("alpha", phases=[_phase("z", age=same), _phase("a", age=same)]),
    )
    hub = build_hub(snap, NOW)
    assert [(i.effort, i.subject) for i in hub.active_phases] == [
        ("alpha", "a"),
        ("alpha", "z"),
        ("beta", "b"),
    ]


def test_r6_running_phase_ranks_first() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            phases=[
                _phase("idle", age=timedelta(minutes=1)),
                _phase("busy", running=True, age=timedelta(days=5)),
            ],
            needs=[_need("n1", age=timedelta(seconds=30))],
        )
    )
    hub = build_hub(snap, NOW)
    assert _subjects(hub.active_phases)[:1] == ["busy"]
    assert [item.running for item in hub.active_phases][:1] == [True]
    assert all(not item.running for item in hub.active_phases[1:])
    assert all(not item.running for item in hub.work_next)


def test_r7_non_running_items_rank_newest_first() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            phases=[_phase("p-old", age=timedelta(days=2))],
            needs=[_need("n-new", age=timedelta(minutes=5))],
            ideas=[_idea("i-mid", age=timedelta(hours=9))],
        )
    )
    hub = build_hub(snap, NOW)
    assert _subjects(hub.work_next) == ["n-new", "i-mid"]
    assert _subjects(hub.active_phases) == ["p-old"]


def test_r8_each_item_has_one_line_reason_naming_recency() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            phases=[
                _phase("busy", running=True),
                _phase("idle", age=timedelta(hours=2)),
            ],
            needs=[_need("n1", age=timedelta(hours=2))],
            ideas=[_idea("i1", age=timedelta(days=3))],
        )
    )
    hub = build_hub(snap, NOW)
    reasons = {item.subject: item.reason for item in [*hub.active_phases, *hub.work_next]}
    assert reasons.get("busy") == "Running now"
    assert reasons.get("idle") == "Updated 2 hours ago"
    assert reasons.get("n1") == "Needs you · updated 2 hours ago"
    assert reasons.get("i1") == "Idea · parked 3 days ago"
    assert reasons and all(reason and "\n" not in reason for reason in reasons.values())


def test_r12_active_phases_use_running_then_recent_order() -> None:
    snap = _snapshot(
        _effort(
            "alpha",
            phases=[
                _phase("old", age=timedelta(days=4)),
                _phase("new", age=timedelta(minutes=10)),
                _phase("busy", running=True, age=timedelta(days=9)),
            ],
        )
    )
    hub = build_hub(snap, NOW)
    assert _subjects(hub.active_phases) == ["busy", "new", "old"]


@pytest.fixture
def ticking_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = itertools.count()
    monkeypatch.setattr(
        record_module,
        "now",
        lambda: (
            datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=next(ticks))
        ).isoformat(),
    )


def _suite_run(
    project: Project,
    phase: str,
    *,
    subject: str | None = None,
    evidence_kind: str = "integration",
    result: str = "pass",
    revision: str = "abcdef0123456789",
) -> None:
    project.create(
        record_type="tuner:check-run",
        subject=subject or f"{phase}-suite",
        payload={
            "criterion_id": f"{phase}-suite",
            "revision": revision,
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "signed_by": "",
            "evidence_kind": evidence_kind,
        },
        body="Suite.\n",
    )


def _suite_label(project: Project, phase: str) -> str:
    snapshot = service.Reader(project).snapshot()
    effort = next(item for item in snapshot.efforts if item.effort == EFFORT)
    return next(row.suite for row in effort.phases if row.subject == phase)


def test_head_evidence_review_latest_failure_at_head_overrides_earlier_pass(
    tmp_path: Path, ticking_clock: None
) -> None:
    project, head = _project_with_phases(tmp_path, "p")
    _review_run(project, "p", head)
    _review_run(project, "p", head, result="fail")

    assert _review_state(project, "p") != "done"


def test_head_evidence_review_latest_pass_at_head_overrides_earlier_failure(
    tmp_path: Path, ticking_clock: None
) -> None:
    project, head = _project_with_phases(tmp_path, "p")
    _review_run(project, "p", head, result="fail")
    _review_run(project, "p", head)

    assert _review_state(project, "p") == "done"


def test_head_evidence_review_ignores_other_phase_and_other_effort_at_same_head(
    tmp_path: Path,
) -> None:
    project, head = _project_with_phases(tmp_path, "p", "q")
    _review_run(project, "q", head)
    _review_run(project, "p", head, effort="other")

    assert _review_state(project, "p") != "done"
    assert _review_state(project, "q") == "done"


def test_head_evidence_suite_names_run_by_criterion_id(tmp_path: Path) -> None:
    project, _ = _project_with_phases(tmp_path, "p")
    _suite_run(project, "p", subject="unrelated")

    assert _suite_label(project, "p") == "suite ok@abcdef0"


def test_head_evidence_suite_ignores_other_evidence_kind(tmp_path: Path) -> None:
    project, _ = _project_with_phases(tmp_path, "p")
    _suite_run(project, "p", evidence_kind="unit")

    assert _suite_label(project, "p") == ""


def test_head_evidence_suite_keeps_legacy_tier2_display(tmp_path: Path) -> None:
    project, _ = _project_with_phases(tmp_path, "p")
    project.create(
        record_type="tuner:check-run",
        subject="p-tier2",
        payload={
            "criterion_id": "p-tier2",
            "revision": "feedface00",
            "result": "pass",
            "effort": EFFORT,
            "method": "check",
            "signed_by": "",
            "evidence_kind": "integration",
        },
        body="Suite.\n",
    )

    assert _suite_label(project, "p") == "suite ok@feedfac"
