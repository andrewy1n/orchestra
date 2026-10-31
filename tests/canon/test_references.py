from __future__ import annotations

import json

import pytest

from orchestra.canon.validation import ValidationError
from conftest import make_task


def log(project, task="t", message="m", **extra):
    return project.create(
        record_type="alpha:log", subject=task, payload={"task": task, "message": message, **extra}
    )


def review(project, task="t", verdict="pass", **extra):
    return project.create(
        record_type="beta:review", subject=task, payload={"task": task, "verdict": verdict, **extra}
    )


def test_subject_reference_resolves_to_an_existing_record(project):
    make_task(project, "t")
    assert log(project)["payload"]["task"] == "t"


def test_missing_subject_is_refused_on_create(project):
    with pytest.raises(ValidationError, match="no alpha:task record with subject 'ghost'"):
        log(project, task="ghost")


def test_reference_into_another_namespace_is_checked(project):
    with pytest.raises(ValidationError, match="no alpha:task record with subject 'ghost'"):
        review(project, task="ghost")
    make_task(project, "t")
    assert review(project)["payload"]["task"] == "t"


def test_reference_to_a_subject_of_the_wrong_type_is_refused(project):
    project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    with pytest.raises(ValidationError, match="no alpha:task record"):
        log(project, task="web")


def test_empty_string_and_empty_list_are_not_checked(project):
    issue = project.create(
        record_type="alpha:issue", subject="q", payload={"summary": "s", "task": ""}
    )
    assert issue["payload"]["task"] == ""
    make_task(project, "t")
    assert review(project, logs=[])["payload"]["logs"] == []


def test_reference_to_a_superseded_subject_resolves_to_its_successor(project):
    task = make_task(project, "t")
    project.supersede(task["id"])
    assert log(project)


def test_multi_type_reference_accepts_either_type(project):
    make_task(project, "t")
    project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    for target in ("t", "web"):
        stored = project.create(
            record_type="alpha:finding", subject=f"f-{target}", payload={"statement": "s", "about": target}
        )
        assert stored["payload"]["about"] == target
    with pytest.raises(ValidationError, match="alpha:task or alpha:config"):
        project.create(
            record_type="alpha:finding", subject="f-x", payload={"statement": "s", "about": "ghost"}
        )


def test_pinned_reference_names_a_record_id(project):
    make_task(project, "t")
    entry = log(project)
    stored = review(project, logs=[entry["id"]])
    assert stored["payload"]["logs"] == [entry["id"]]


def test_pinned_reference_rejects_a_subject_and_an_unknown_id(project):
    make_task(project, "t")
    log(project)
    with pytest.raises(ValidationError, match="no alpha:log record with id 't'"):
        review(project, logs=["t"])
    with pytest.raises(ValidationError, match="no alpha:log record with id"):
        review(project, logs=["rec-00000000-0000-0000-0000-000000000000"])


def test_pinned_reference_rejects_an_id_of_the_wrong_type(project):
    task = make_task(project, "t")
    with pytest.raises(ValidationError, match="no alpha:log record"):
        review(project, logs=[task["id"]])


def test_pinned_reference_checks_every_list_item(project):
    make_task(project, "t")
    entry = log(project)
    with pytest.raises(ValidationError, match=r"logs'\[1\]"):
        review(project, logs=[entry["id"], "rec-00000000-0000-0000-0000-000000000000"])


def test_depends_on_checks_each_subject(project):
    make_task(project, "a")
    stored = make_task(project, "b", depends_on=["a"])
    assert stored["payload"]["depends_on"] == ["a"]
    with pytest.raises(ValidationError, match="depends_on'\\[0\\]: no alpha:task record"):
        make_task(project, "c", depends_on=["ghost"])


def test_reference_is_checked_on_update(project):
    make_task(project, "t")
    entry = project.create(
        record_type="alpha:issue", subject="q", payload={"summary": "s", "task": "t"}
    )
    with pytest.raises(ValidationError, match="no alpha:task record with subject 'ghost'"):
        project.update(entry["id"], payload={"task": "ghost"})
    moved = project.update(entry["id"], payload={"task": ""})
    assert moved["payload"]["task"] == ""


def test_reference_is_checked_on_supersede(project):
    make_task(project, "t")
    task = make_task(project, "u")
    with pytest.raises(ValidationError, match="depends_on'\\[0\\]: no alpha:task record"):
        project.supersede(task["id"], payload={"depends_on": ["ghost"]})
    assert project.get(task["id"])["lifecycle_state"] == "planned"
    result = project.supersede(task["id"], payload={"depends_on": ["t"]})
    assert result["record"]["payload"]["depends_on"] == ["t"]


def test_reference_is_checked_on_correct(project):
    make_task(project, "t")
    entry = log(project)
    with pytest.raises(ValidationError, match="no alpha:task record with subject 'ghost'"):
        project.correct(entry["id"], payload={"task": "ghost"})
    result = project.correct(entry["id"], payload={"message": "better"})
    assert result["record"]["payload"]["task"] == "t"


def test_reference_is_checked_on_each_apply_operation(project):
    make_task(project, "t")
    entry = log(project)
    old = project.create(
        record_type="alpha:issue", subject="q", payload={"summary": "s", "task": "t"}
    )
    cfg = project.create(
        record_type="alpha:finding", subject="f", payload={"statement": "s"}
    )
    ops = [
        {"op": "create", "type": "alpha:log", "subject": "t", "payload": {"task": "ghost", "message": "m"}},
        {"op": "update", "id": old["id"], "payload": {"task": "ghost"}},
        {"op": "supersede", "id": make_task(project, "u")["id"], "payload": {"depends_on": ["ghost"]}},
        {"op": "correct", "id": entry["id"], "payload": {"task": "ghost"}},
        {"op": "update", "id": cfg["id"], "payload": {"evidence": ["rec-00000000-0000-0000-0000-000000000000"]}},
    ]
    results = project.apply(ops)
    assert [r["ok"] for r in results] == [False] * 5
    assert {r["error"] for r in results} == {"validation"}
    assert all("no alpha:" in r["message"] for r in results)


def test_apply_sees_records_created_earlier_in_the_batch(project):
    results = project.apply(
        [
            {"op": "create", "type": "alpha:task", "subject": "t", "payload": {"title": "t"}},
            {"op": "create", "type": "alpha:log", "subject": "t", "payload": {"task": "t", "message": "m"}},
            {"op": "create", "type": "beta:review", "subject": "t", "payload": {"task": "t", "verdict": "pass"}},
        ]
    )
    assert [r["ok"] for r in results] == [True, True, True]


def test_reference_to_a_type_that_is_not_installed_is_refused(project):
    assert project.schemas().types.get("gamma:thing") is None
    store_root = project.store_path
    snapshot = store_root / "schemas" / "beta.json"
    data = json.loads(snapshot.read_text())
    data["types"]["review"]["fields"]["other"] = {"ref": "gamma:thing", "optional": True}
    snapshot.write_text(json.dumps(data))
    make_task(project, "t")
    with pytest.raises(ValidationError, match="type gamma:thing is not installed"):
        review(project, other="x")
    assert review(project, other="")
