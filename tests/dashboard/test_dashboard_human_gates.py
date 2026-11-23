from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import make_project

from dashboard.backend import dismiss, journal, store
from dashboard.backend.server import service
from dashboard.backend.snapshot import NEEDS_ORDER, NeedsYouItem
from orchestra.canon import project as project_mod
from orchestra.canon import record as record_mod
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.score.workflow.workflow_blockers import human_gates

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
EFFORT = "alpha"

At = Callable[[int], None]


@pytest.fixture()
def at(monkeypatch: pytest.MonkeyPatch) -> At:
    stamp = [NOW - timedelta(hours=10)]

    def now() -> str:
        return stamp[0].isoformat()

    def set_minutes(minutes: int) -> None:
        stamp[0] = NOW - timedelta(hours=10) + timedelta(minutes=minutes)

    monkeypatch.setattr(record_mod, "now", now)
    monkeypatch.setattr(project_mod, "now", now)
    return set_minutes


@pytest.fixture()
def project(tmp_path: Path, at: At) -> Project:
    target = make_project(tmp_path)
    _create(target, "score:effort", EFFORT, {"goal": "ship alpha", "kind": "deliver"})
    return target


def _create(
    target: Project, record_type: str, subject: str, payload: JsonObject, body: str | None = None
) -> Record:
    if body is None:
        body = "\n\n".join(
            f"## {section}\n\nText." for section in target.schemas().types[record_type].sections
        )
    return target.create(record_type=record_type, subject=subject, payload=payload, body=body)


def _question(target: Project, subject: str, scope: str, *, blocking: bool) -> Record:
    payload: JsonObject = {"scope": scope, "owner": "human", "blocking": blocking}
    return _create(target, "score:continuity-question", subject, payload)


def _finding(target: Project, subject: str, needs: str, effort: str = EFFORT) -> Record:
    return _create(
        target,
        "tuner:finding",
        subject,
        {
            "claim": f"claim of {subject}",
            "basis": "observed",
            "needs": needs,
            "effort": effort,
            "invalidated_when": "decision recorded",
        },
    )


def _acceptance(target: Project, subject: str) -> Record:
    return _create(
        target,
        "score:acceptance",
        subject,
        {"method": "manual", "effort": EFFORT, "verify_command": "true"},
    )


def _run(target: Project, subject: str, criterion: str, signed_by: str) -> Record:
    return _create(
        target,
        "tuner:check-run",
        subject,
        {
            "criterion_id": criterion,
            "revision": "abc",
            "result": "pass",
            "effort": EFFORT,
            "method": "manual",
            "signed_by": signed_by,
        },
    )


def _needs(target: Project) -> list[NeedsYouItem]:
    snapshot = service.Reader(target).cache.work_current(NOW)
    return [item for view in snapshot.efforts if view.effort == EFFORT for item in view.needs_you]


def _kinds(target: Project) -> list[tuple[str, str]]:
    return [(item.kind, item.id) for item in _needs(target)]


def test_r13_dashboard_lists_blocking_question(project: Project) -> None:
    question = _question(project, EFFORT, "which backend", blocking=True)
    (item,) = _needs(project)
    assert (item.kind, item.id, item.subject, item.text) == (
        "blocking-question",
        question["id"],
        EFFORT,
        "which backend",
    )
    assert item.record_type == "score:continuity-question"
    assert item.revision == question["revision"]


def test_r13_dashboard_lists_non_blocking_question_as_open_question(project: Project) -> None:
    question = _question(project, EFFORT, "which style", blocking=False)
    assert _kinds(project) == [("open-question", question["id"])]


def test_r13_dashboard_omits_answered_question(project: Project) -> None:
    question = _question(project, EFFORT, "settled", blocking=True)
    project.update(question["id"], transition="answered")
    assert _needs(project) == []


@pytest.mark.parametrize("state", ["asserted", "supported", "disputed"])
def test_r13_dashboard_lists_needs_human_finding_in_open_states(
    project: Project, state: str
) -> None:
    finding = _finding(project, "decide", "human")
    if state != "asserted":
        project.update(finding["id"], transition=state)
    (item,) = _needs(project)
    assert (item.kind, item.id, item.subject, item.text) == (
        "needs-human",
        finding["id"],
        "decide",
        "claim of decide",
    )
    assert item.record_type == "tuner:finding"


@pytest.mark.parametrize("state", ["refuted", "retracted"])
def test_r13_dashboard_omits_closed_needs_human_finding(project: Project, state: str) -> None:
    finding = _finding(project, "decide", "human")
    project.update(finding["id"], transition=state)
    assert _needs(project) == []


def test_r13_dashboard_omits_finding_that_needs_no_human(project: Project) -> None:
    _finding(project, "agent-only", "agent")
    _finding(project, "done", "none")
    assert _needs(project) == []


def test_r13_dashboard_lists_unsigned_manual_check(project: Project) -> None:
    _acceptance(project, "accept-a")
    run = _run(project, "run-a", "accept-a", "")
    (item,) = _needs(project)
    assert (item.kind, item.id) == ("unsigned-check", run["id"])
    assert item.record_type == "tuner:check-run"
    assert item.revision == run["revision"]


def test_r13_dashboard_omits_signed_manual_check(project: Project) -> None:
    _acceptance(project, "accept-a")
    _run(project, "run-a", "accept-a", "alice")
    assert _needs(project) == []


def test_r13_dashboard_lists_unsigned_run_recorded_against_acceptance_id(
    project: Project,
) -> None:
    acceptance = _acceptance(project, "accept-a")
    run = _run(project, "run-a", acceptance["id"], "")
    (item,) = _needs(project)
    assert (item.kind, item.id, item.subject) == ("unsigned-check", run["id"], "accept-a")


def test_r13_dashboard_omits_unsigned_run_after_later_signed_run(project: Project, at: At) -> None:
    _acceptance(project, "accept-a")
    at(1)
    _run(project, "run-unsigned", "accept-a", "")
    at(2)
    _run(project, "run-signed", "accept-a", "alice")
    assert _needs(project) == []


def test_r13_dashboard_lists_unsigned_run_after_earlier_signed_run(
    project: Project, at: At
) -> None:
    _acceptance(project, "accept-a")
    at(1)
    _run(project, "run-signed", "accept-a", "alice")
    at(2)
    unsigned = _run(project, "run-unsigned", "accept-a", "")
    assert _kinds(project) == [("unsigned-check", unsigned["id"])]


def test_r13_dashboard_omits_corrected_unsigned_run(project: Project, at: At) -> None:
    _acceptance(project, "accept-a")
    at(1)
    run = _run(project, "run-a", "accept-a", "")
    at(2)
    project.correct(run["id"], payload={"signed_by": "alice"})
    assert _needs(project) == []


def test_r13_dashboard_keeps_needs_order_and_item_fields(project: Project) -> None:
    _question(project, EFFORT, "open one", blocking=False)
    _acceptance(project, "accept-a")
    _run(project, "run-a", "accept-a", "")
    _finding(project, "decide", "human")
    _question(project, EFFORT, "blocking one", blocking=True)
    kinds = [item.kind for item in _needs(project)]
    assert sorted(kinds, key=NEEDS_ORDER.index) == kinds
    assert set(kinds) == {"blocking-question", "needs-human", "unsigned-check", "open-question"}
    assert NEEDS_ORDER == (
        "blocking-question",
        "loop-route",
        "integration",
        "merge-branch",
        "needs-human",
        "unsigned-check",
        "open-question",
    )
    assert tuple(NeedsYouItem.__dataclass_fields__) == (
        "kind",
        "id",
        "subject",
        "text",
        "record_type",
        "body",
        "task_id",
        "phase",
        "requirement",
        "status",
        "next",
        "result",
        "revision",
        "updated_at",
    )


@pytest.mark.parametrize(
    ("needs", "state", "expected_open"),
    [
        ("human", "asserted", True),
        ("human", "supported", True),
        ("human", "disputed", True),
        ("human", "refuted", False),
        ("human", "retracted", False),
        ("none", "asserted", False),
        ("none", "supported", False),
        ("none", "disputed", False),
        ("agent", "asserted", False),
    ],
)
def test_r14_journal_marks_finding_open_by_needs_and_state(
    project: Project, needs: str, state: str, expected_open: bool
) -> None:
    finding = _finding(project, "j-finding", needs)
    if state != "asserted":
        project.update(finding["id"], transition=state)
    items = journal.load_journal(project, EFFORT)
    open_ids = {item.id for item in items if item.open}
    assert (finding["id"] in open_ids) is expected_open


KIND_RECORD_TYPE = {
    "blocking-question": "score:continuity-question",
    "open-question": "score:continuity-question",
    "needs-human": "tuner:finding",
    "unsigned-check": "tuner:check-run",
}


def _seed_every_kind(target: Project) -> dict[str, Record]:
    blocking = _question(target, EFFORT, "blocking", blocking=True)
    open_question = _question(target, "alpha-open", "open", blocking=False)
    finding = _finding(target, "decide", "human")
    _acceptance(target, "accept-a")
    run = _run(target, "run-a", "accept-a", "")
    return {
        "blocking-question": blocking,
        "open-question": open_question,
        "needs-human": finding,
        "unsigned-check": run,
    }


def _bare_item(kind: str, record: Record) -> NeedsYouItem:
    return NeedsYouItem(kind, record["id"], record["subject"], "", revision=record["revision"])


@pytest.mark.parametrize("kind", sorted(KIND_RECORD_TYPE))
def test_r15_current_revision_resolves_record_type_from_kind(project: Project, kind: str) -> None:
    seeded = _seed_every_kind(project)
    gates = {gate.kind: gate for gate in human_gates(store.catalog_records(project))}
    assert gates[kind].clears == KIND_RECORD_TYPE[kind]
    item = _bare_item(kind, seeded[kind])
    assert item.record_type == ""
    assert dismiss._current_revision(project, item) == seeded[kind]["revision"]


@pytest.mark.parametrize("kind", sorted(KIND_RECORD_TYPE))
def test_r15_dismiss_item_with_empty_record_type_clears_each_kind(
    project: Project, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = _seed_every_kind(project)
    item = _bare_item(kind, seeded[kind])
    monkeypatch.setenv(dismiss.DEFAULT_SIGNER_ENV, "alice")
    dismiss.dismiss_item(project, item)
    remaining = {gate.record["id"] for gate in human_gates(store.catalog_records(project))}
    assert seeded[kind]["id"] not in remaining
    assert len(remaining) == len(KIND_RECORD_TYPE) - 1


def test_r15_stale_revision_still_refuses_after_type_lookup(project: Project) -> None:
    question = _question(project, EFFORT, "which backend", blocking=True)
    item = _bare_item("blocking-question", question)
    project.update(question["id"], payload={"scope": "changed"})
    with pytest.raises(dismiss.DismissError, match="stale revision"):
        dismiss.dismiss_item(project, item, action=dismiss.ACTION_REJECT)
