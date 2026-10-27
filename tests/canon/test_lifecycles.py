from __future__ import annotations

import pytest

from canon.lifecycle import LIFECYCLES, terminal_success_state
from canon.store import StoreError
from canon.validation import ValidationError
from conftest import make_task

PATHS = {
    "current": ("alpha:config", {"title": "c", "level": 1}),
    "staged": ("alpha:task", {"title": "t"}),
    "event": ("alpha:log", None),
    "question": ("alpha:issue", {"summary": "s"}),
    "claim": ("alpha:finding", {"statement": "s"}),
}

ALLOWED = {
    "current": {"active": {"superseded"}},
    "staged": {
        "planned": {"in_progress", "withdrawn", "superseded"},
        "in_progress": {"done", "withdrawn", "superseded"},
        "done": {"superseded"},
        "withdrawn": set(),
        "superseded": set(),
    },
    "event": {"recorded": set()},
    "question": {
        "open": {"answered", "deferred", "closed"},
        "deferred": {"open", "closed"},
        "answered": set(),
        "closed": set(),
    },
    "claim": {
        "asserted": {"supported", "disputed", "refuted", "retracted"},
        "supported": {"disputed", "refuted", "retracted"},
        "disputed": {"supported", "refuted", "retracted"},
        "refuted": set(),
        "retracted": set(),
    },
}

INITIAL = {
    "current": "active",
    "staged": "planned",
    "event": "recorded",
    "question": "open",
    "claim": "asserted",
}


def test_lifecycle_tables_match_the_spec():
    assert set(LIFECYCLES) == set(ALLOWED)
    for name, table in ALLOWED.items():
        lifecycle = LIFECYCLES[name]
        assert lifecycle.initial == INITIAL[name]
        for src in lifecycle.states:
            for dest in lifecycle.states:
                assert lifecycle.allows(src, dest) == (dest in table.get(src, set())), (src, dest)


def test_each_lifecycle_starts_in_its_initial_state(project):
    for name, (record_type, payload) in PATHS.items():
        if name == "event":
            make_task(project, "for-log")
            payload = {"task": "for-log", "message": "m"}
        record = project.create(record_type=record_type, subject=f"{name}-1", payload=payload)
        assert record["lifecycle_state"] == INITIAL[name]


def _fresh(project, name, suffix):
    record_type, payload = PATHS[name]
    subject = f"{name}-{suffix}"
    if name == "staged":
        payload = {"title": subject}
    return project.create(record_type=record_type, subject=subject, payload=payload)


@pytest.mark.parametrize("name", ["staged", "question", "claim"])
def test_allowed_and_refused_transitions(project, name):
    lifecycle = LIFECYCLES[name]
    n = 0
    for src in lifecycle.states:
        for dest in lifecycle.states:
            if src == "superseded" or dest == "superseded":
                continue
            n += 1
            record = _reach(project, name, src, n)
            if lifecycle.allows(src, dest):
                moved = project.update(record["id"], transition=dest)
                assert moved["lifecycle_state"] == dest
            else:
                with pytest.raises(ValidationError, match="invalid transition"):
                    project.update(record["id"], transition=dest)
                assert project.get(record["id"])["lifecycle_state"] == src


def _reach(project, name, state, n):
    record = _fresh(project, name, n)
    for hop in _route(name, state):
        record = project.update(record["id"], transition=hop)
    assert record["lifecycle_state"] == state
    return record


def _route(name, state):
    lifecycle = LIFECYCLES[name]
    if state == lifecycle.initial:
        return []
    queue = [(lifecycle.initial, [])]
    seen = {lifecycle.initial}
    while queue:
        current, path = queue.pop(0)
        for dest in lifecycle.transitions.get(current, ()):
            if dest == "superseded" or dest in seen:
                continue
            if dest == state:
                return path + [dest]
            seen.add(dest)
            queue.append((dest, path + [dest]))
    raise AssertionError(f"{state} unreachable")


def test_unknown_state_is_refused(project):
    record = make_task(project, "t")
    with pytest.raises(ValidationError, match="invalid transition"):
        project.update(record["id"], transition="finished")


def test_update_never_transitions_to_superseded(project):
    for name in ("current", "staged"):
        record = _fresh(project, name, "s")
        with pytest.raises(ValidationError, match="supersede operation"):
            project.update(record["id"], transition="superseded")


def test_current_allows_one_active_record_per_subject(project):
    first = project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    with pytest.raises(ValidationError, match="supersede"):
        project.create(record_type="alpha:config", subject="web", payload={"title": "b", "level": 2})
    other = project.create(record_type="alpha:config", subject="api", payload={"title": "b", "level": 2})
    assert other["lifecycle_state"] == "active"
    result = project.supersede(first["id"], payload={"level": 3})
    assert result["predecessor"]["lifecycle_state"] == "superseded"
    assert result["record"]["lifecycle_state"] == "active"
    assert result["record"]["id"] != first["id"]
    assert result["record"]["payload"] == {"title": "a", "level": 3}
    assert result["record"]["relationships"] == {"supersedes": [first["id"]]}
    again = project.create(record_type="alpha:config", subject="web2", payload={"title": "b", "level": 2})
    assert again["subject"] == "web2"


def test_current_cannot_supersede_a_superseded_record(project):
    first = project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    project.supersede(first["id"])
    with pytest.raises(ValidationError, match="invalid transition"):
        project.supersede(first["id"])


@pytest.mark.parametrize("state", ["planned", "in_progress", "done"])
def test_staged_supersede_from_each_live_state(project, state):
    task = _reach(project, "staged", state, 1)
    result = project.supersede(task["id"], payload={"title": "again"})
    assert result["predecessor"]["lifecycle_state"] == "superseded"
    assert result["record"]["lifecycle_state"] == "planned"
    assert result["record"]["subject"] == task["subject"]


def test_staged_withdrawn_cannot_be_superseded(project):
    task = _reach(project, "staged", "withdrawn", 1)
    with pytest.raises(ValidationError, match="invalid transition"):
        project.supersede(task["id"])


@pytest.mark.parametrize("name", ["question", "claim"])
def test_question_and_claim_have_no_supersede(project, name):
    record = _fresh(project, name, 1)
    with pytest.raises(ValidationError, match="invalid transition"):
        project.supersede(record["id"])


def test_event_is_append_only(project):
    make_task(project, "t")
    log = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "m"})
    with pytest.raises(ValidationError, match="cannot be mutated"):
        project.update(log["id"], payload={"message": "other"})
    with pytest.raises(ValidationError, match="cannot be mutated"):
        project.update(log["id"], transition="recorded")
    with pytest.raises(ValidationError, match="cannot be mutated"):
        project.supersede(log["id"])


def test_events_may_share_a_subject(project):
    make_task(project, "t")
    for message in ("one", "two", "three"):
        project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": message})
    assert len(project.list("alpha:log")) == 3


def test_event_correct_writes_a_successor_and_marks_the_original(project):
    make_task(project, "t")
    log = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "wrong"})
    result = project.correct(log["id"], payload={"message": "right"})
    assert result["record"]["relationships"] == {"corrects": [log["id"]]}
    assert result["record"]["payload"]["message"] == "right"
    assert result["predecessor"]["payload"]["message"] == "wrong"
    assert project.get(log["id"])["lifecycle_state"] == "recorded"
    assert project.derived()[log["id"]]["corrected"] is True
    assert "corrected" not in project.derived().get(result["record"]["id"], {})


def test_event_cannot_be_corrected_twice(project):
    make_task(project, "t")
    log = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "a"})
    second = project.correct(log["id"], payload={"message": "b"})["record"]
    with pytest.raises(ValidationError, match="already corrected"):
        project.correct(log["id"], payload={"message": "c"})
    third = project.correct(second["id"], payload={"message": "c"})["record"]
    assert third["relationships"] == {"corrects": [second["id"]]}


@pytest.mark.parametrize("name", ["current", "staged", "question", "claim"])
def test_non_event_types_cannot_be_corrected(project, name):
    record = _fresh(project, name, 1)
    with pytest.raises(ValidationError, match="successor-record correction"):
        project.correct(record["id"])


def test_terminal_success_state():
    assert terminal_success_state(LIFECYCLES["staged"]) == "done"
    assert terminal_success_state(LIFECYCLES["event"]) is None
    assert terminal_success_state(LIFECYCLES["current"]) is None
    assert terminal_success_state(LIFECYCLES["question"]) in {"answered", "closed"}


def test_unknown_type_is_refused(project):
    with pytest.raises(StoreError, match="unknown record type"):
        project.create(record_type="alpha:nope", subject="x", payload={})
