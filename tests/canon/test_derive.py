from __future__ import annotations

from orchestra.canon.backend import open_backend
from orchestra.canon.derive import attach_derived_all, compute_derived, compute_inverse
from conftest import advance, make_task


def derived_of(project, record):
    return project.derived().get(record["id"], {})


def test_a_task_without_dependencies_is_ready_in_wave_one(project):
    task = make_task(project, "a")
    assert derived_of(project, task) == {"ready": True, "wave": 1}


def test_ready_waits_for_the_dependency_to_be_done(project):
    a = make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    assert derived_of(project, b) == {"ready": False, "wave": 2}
    advance(project, a, "in_progress")
    assert derived_of(project, b)["ready"] is False
    project.update(a["id"], transition="done")
    assert derived_of(project, b) == {"ready": True, "wave": 2}


def test_waves_follow_the_longest_dependency_chain(project):
    make_task(project, "a")
    make_task(project, "b", depends_on=["a"])
    make_task(project, "c", depends_on=["a"])
    d = make_task(project, "d", depends_on=["b", "c"])
    e = make_task(project, "e", depends_on=["d", "a"])
    assert derived_of(project, d)["wave"] == 3
    assert derived_of(project, e)["wave"] == 4


def test_a_withdrawn_dependency_never_satisfies_its_dependents(project):
    a = make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    project.update(a["id"], transition="withdrawn")
    assert derived_of(project, b)["ready"] is False


def test_a_superseded_dependency_resolves_to_its_successor(project):
    a = make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    successor = project.supersede(a["id"])["record"]
    assert derived_of(project, b)["ready"] is False
    advance(project, successor, "in_progress", "done")
    assert derived_of(project, b)["ready"] is True
    assert derived_of(project, b)["wave"] == 2


def test_waves_report_cycles_as_none(project):
    a = make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    c = make_task(project, "c", depends_on=["b"])
    project.update(a["id"], payload={"depends_on": ["c"]})
    d = make_task(project, "d", depends_on=["c"])
    assert derived_of(project, a)["wave"] is None
    assert derived_of(project, b)["wave"] is None
    assert derived_of(project, c)["wave"] is None
    assert derived_of(project, d)["wave"] is None
    assert derived_of(project, d)["ready"] is False


def test_only_staged_types_get_ready_and_wave(project):
    project.create(record_type="alpha:config", subject="c", payload={"title": "t", "level": 1})
    assert project.derived() == {}


def test_corrected_and_inverse_links(project):
    make_task(project, "t")
    log = project.create(
        record_type="alpha:log", subject="t", payload={"task": "t", "message": "a"}
    )
    corrector = project.correct(log["id"], payload={"message": "b"})["record"]
    derived = project.derived()
    assert derived[log["id"]] == {
        "referenced_by": {"corrects": [corrector["id"]]},
        "corrected": True,
    }
    assert corrector["id"] not in derived

    config = project.create(
        record_type="alpha:config", subject="c", payload={"title": "t", "level": 1}
    )
    newer = project.supersede(config["id"])["record"]
    assert project.derived()[config["id"]] == {"referenced_by": {"supersedes": [newer["id"]]}}


def test_a_dependency_lists_its_dependents_in_referenced_by(project):
    a = make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    c = make_task(project, "c", depends_on=["a"])
    assert derived_of(project, a)["referenced_by"] == {"depends_on": sorted([b["id"], c["id"]])}
    assert "referenced_by" not in derived_of(project, b)


def test_compute_inverse_sorts_sources():
    records = [
        {"id": "rec-b", "relationships": {"supersedes": ["rec-x"]}},
        {"id": "rec-a", "relationships": {"supersedes": ["rec-x"]}},
    ]
    assert compute_inverse(records) == {"rec-x": {"supersedes": ["rec-a", "rec-b"]}}


def test_derived_values_are_never_persisted(project):
    task = make_task(project, "a")
    attached = attach_derived_all(project.records(), project.derived())
    assert attached[0]["derived"] == {"ready": True, "wave": 1}
    assert "derived" not in project.get(task["id"])
    backend = open_backend(project.store_path)
    assert all("derived" not in record for record in backend.iter_records())
    assert all("derived" not in op["record"] for _, ops in backend.iter_chains() for op in ops)


def test_list_filters_on_derived_values(cli, project):
    a = make_task(project, "a")
    make_task(project, "b", depends_on=["a"])
    make_task(project, "c")
    ready = cli.ok("list", "--type", "task", "--where", "derived.ready=true", "--fields", "subject")
    assert sorted(r["subject"] for r in ready["records"]) == ["a", "c"]
    advance(project, a, "in_progress", "done")
    ready = cli.ok(
        "list",
        "--type",
        "task",
        "--state",
        "planned",
        "--where",
        "derived.ready=true",
        "--fields",
        "subject",
    )
    assert sorted(r["subject"] for r in ready["records"]) == ["b", "c"]
    waves = cli.ok(
        "list",
        "--type",
        "task",
        "--order-by",
        "derived.wave",
        "--desc",
        "--fields",
        "subject,derived.wave",
    )
    assert waves["records"][0] == {"subject": "b", "derived.wave": 2}


def test_has_inbound_filters_on_relationship_type(cli, project):
    make_task(project, "t")
    first = project.create(
        record_type="alpha:log", subject="t", payload={"task": "t", "message": "a"}
    )
    project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "b"})
    project.correct(first["id"], payload={"message": "c"})
    out = cli.ok("list", "--type", "log", "--has-inbound", "corrects", "--fields", "id")
    assert [r["id"] for r in out["records"]] == [first["id"]]


def test_compute_derived_accepts_an_empty_record_set(project):
    assert compute_derived([], project.schemas()) == {}
