from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from canon.merge import MergeError, merge_store
from canon.oplog import fold, read_ops
from canon.project import open_store
from canon.record_file import load_record
from canon.revision import compute_revision
from canon.store import Store
from conftest import ALPHA, BETA, PLAN_BODY, make_git_repo


def renamed_module(module: dict, namespace: str, others: dict[str, str] | None = None) -> dict:
    text = json.dumps(module)
    for old, new in {module["namespace"]: namespace, **(others or {})}.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f'"{old}:', f'"{new}:')
    return json.loads(text)


@pytest.fixture
def source(cli, tmp_path):
    root = make_git_repo(tmp_path / "source")
    cli("init", "--schemas", "alpha,beta", root=root)
    ok = lambda *args: cli(*args, root=root)
    for args in (
        ("create", "--type", "alpha:task", "--subject", "t1", "--payload", '{"title": "one"}'),
        ("create", "--type", "alpha:config", "--subject", "c1", "--payload", '{"title": "c", "level": 1}'),
    ):
        assert ok(*args).code == 0
    assert ok("update", "--type", "alpha:task", "--subject", "t1", "--transition", "in_progress").code == 0
    assert ok("update", "--type", "alpha:config", "--subject", "c1", "--set", "level=2").code == 0
    log = json.loads(
        ok("create", "--type", "alpha:log", "--subject", "t1", "--payload",
           '{"task": "t1", "message": "m"}').out
    )["record"]
    review = ["create", "--type", "beta:review", "--subject", "t1", "--payload",
              json.dumps({"task": "t1", "verdict": "pass", "logs": [log["id"]]})]
    assert ok(*review).code == 0
    assert ok("create", "--type", "beta:plan", "--subject", "p1", "--payload", '{"goal": "g"}',
              "--body", PLAN_BODY).code == 0
    assert open_store(root).validate() == []
    return open_store(root)


def read_all(project):
    return {record["id"]: record for record in project.records()}


def merge(target, source, **kwargs):
    return merge_store(Store(target.store_path), target.schemas(), source.store_path, **kwargs)


def tree(project) -> dict[str, str]:
    root = project.store_path
    return {
        str(path.relative_to(root)): path.read_text()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).parts[0] in {"records", "history", "log"}
    }


def test_plain_merge_copies_records_history_and_logs(project, source):
    summary = merge(project, source)
    assert summary["status"] == "valid"
    assert read_all(project) == read_all(source)
    assert summary["types"]["alpha:task"] == {"records": 1, "history": 1, "log": 2}
    assert summary["totals"]["records"] == 5
    for path, text in tree(source).items():
        assert (project.store_path / path).read_text() == text
    assert project.validate() == []


def test_merge_keeps_existing_target_records(project, source):
    own = project.create(record_type="alpha:task", subject="mine", payload={"title": "m"})
    merge(project, source)
    assert project.get(own["id"]) == own
    assert len(project.records()) == 6


def test_cli_merge_prints_table_and_json(cli, project, source):
    result = cli("merge", str(source.store_path))
    assert result.code == 0
    assert "alpha:task\t1\t1\t2" in result.out and "validation: valid" in result.out
    again = cli("merge", str(source.store_path), "--format", "json")
    assert again.code == 1 and again.json["error"] == "merge"


def test_cli_merge_json_summary(cli, project, source):
    summary = cli.ok("merge", str(source.store_path), "--format", "json")
    assert summary["status"] == "valid" and summary["renamed_subjects"] == []
    assert summary["types"]["beta:review"]["records"] == 1


class TestNamespaceMapping:
    @pytest.fixture
    def target(self, site, tmp_path, cli):
        site.publish(renamed_module(ALPHA, "zed"))
        site.publish(renamed_module(BETA, "yon", {"alpha": "zed"}))
        root = make_git_repo(tmp_path / "target")
        assert cli("init", "--schemas", "zed,yon", root=root).code == 0
        return open_store(root)

    def test_types_directories_history_and_logs_are_rewritten(self, target, source):
        summary = merge(target, source, namespaces={"alpha": "zed", "beta": "yon"})
        assert summary["status"] == "valid"
        assert target.validate() == []
        store = target.store_path
        names = {p.name for p in (store / "records").iterdir()}
        assert names == {"zed__task", "zed__config", "zed__log", "yon__review", "yon__plan"}
        assert {p.name for p in (store / "history").iterdir()} >= {"zed__task", "zed__config"}
        assert {p.name for p in (store / "log").iterdir()} == names
        for record in target.records():
            assert record["record_type"].split(":")[0] in {"zed", "yon"}
            assert record["revision"] == compute_revision(record)
        for snapshot in Store(store).iter_history():
            assert snapshot[1]["record_type"].startswith(("zed:", "yon:"))
        for record in target.records():
            chain = store / "log" / record["record_type"].replace(":", "__") / record["id"]
            assert fold(read_ops(chain)) == record
        review = target.list("yon:review")[0]
        assert review["payload"]["task"] == "t1"
        assert review["payload"]["logs"] == [target.list("zed:log")[0]["id"]]

    def test_unmapped_namespace_keeps_its_name(self, project, source, site, tmp_path, cli):
        site.publish(renamed_module(ALPHA, "zed"))
        root = make_git_repo(tmp_path / "t2")
        assert cli("init", "--schemas", "zed,beta", root=root).code == 0
        other = open_store(root)
        other_beta = copy.deepcopy(BETA)
        other_beta["types"]["review"]["fields"]["task"] = {"ref": "zed:task"}
        other_beta["types"]["review"]["fields"]["logs"]["list"]["ref"] = "zed:log"
        site.publish(other_beta)
        assert cli("schemas", "sync", root=root).code == 0
        summary = merge(other, source, namespaces={"alpha": "zed"})
        assert summary["status"] == "valid"
        assert other.list("beta:plan")

    def test_cli_namespace_option(self, cli, target, source):
        result = cli("merge", str(source.store_path), "--namespace", "alpha=zed", "--namespace", "beta=yon",
                     "--format", "json", root=target.project_root)
        assert result.code == 0, result.out
        assert result.json["types"]["zed:task"]["records"] == 1


class TestSubjectRename:
    def test_references_to_a_renamed_subject_are_rewritten(self, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        summary = merge(project, source, subject_renames={("alpha:task", "t1"): "t1-src"})
        assert summary["status"] == "valid"
        assert summary["renamed_subjects"] == [
            {"record_type": "alpha:task", "old": "t1", "new": "t1-src", "records": 1}
        ]
        assert project.resolve("alpha:task", "t1-src")["payload"]["title"] == "one"
        assert project.list("beta:review")[0]["payload"]["task"] == "t1-src"
        assert project.list("alpha:log")[0]["payload"]["task"] == "t1-src"
        assert project.validate() == []
        for record in project.list("alpha:task"):
            assert record["revision"] == compute_revision(record)

    def test_history_and_logs_follow_the_new_subject(self, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        merge(project, source, subject_renames={("alpha:task", "t1"): "t1-src"})
        moved = project.resolve("alpha:task", "t1-src")
        chain = project.store_path / "log" / "alpha__task" / moved["id"]
        assert fold(read_ops(chain)) == moved
        assert all(op["record"]["subject"] == "t1-src" for op in read_ops(chain))
        history = project.store_path / "history" / "alpha__task" / moved["id"]
        for path in history.iterdir():
            assert load_record(path.read_text(), path)["subject"] == "t1-src"

    def test_cli_rename_subject_option(self, cli, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        result = cli("merge", str(source.store_path), "--rename-subject", "alpha:task:t1=t1-src",
                     "--format", "json")
        assert result.code == 0, result.out
        assert result.json["renamed_subjects"][0]["new"] == "t1-src"

    def test_rename_follows_the_namespace_mapping(self, project, source):
        summary = merge(project, source, subject_renames={("alpha:task", "t1"): "t2"})
        assert summary["renamed_subjects"][0]["record_type"] == "alpha:task"
        assert project.list("beta:review")[0]["payload"]["task"] == "t2"


class TestAborts:
    def test_id_collision_writes_nothing(self, project, source):
        record = source.list("alpha:config")[0]
        Store(project.store_path).create_record({**record, "subject": "other"})
        before = tree(project)
        with pytest.raises(MergeError, match=record["id"]) as caught:
            merge(project, source)
        assert caught.value.details["id_conflicts"] == [record["id"]]
        assert tree(project) == before

    def test_subject_collision_on_a_non_event_type_writes_nothing(self, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        before = tree(project)
        with pytest.raises(MergeError) as caught:
            merge(project, source)
        assert caught.value.details["subject_conflicts"] == [
            {"record_type": "alpha:task", "subject": "t1"}
        ]
        assert tree(project) == before

    def test_cli_reports_each_conflict(self, cli, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        project.create(record_type="beta:plan", subject="p1", payload={"goal": "x"}, body=PLAN_BODY)
        result = cli("merge", str(source.store_path), "--format", "json")
        assert result.code == 1
        assert result.json["subject_conflicts"] == [
            {"record_type": "alpha:task", "subject": "t1"},
            {"record_type": "beta:plan", "subject": "p1"},
        ]

    def test_event_subjects_may_collide(self, project, source):
        project.create(record_type="alpha:task", subject="t1", payload={"title": "mine"})
        project.create(record_type="alpha:log", subject="t1", payload={"task": "t1", "message": "x"})
        summary = merge(project, source, subject_renames={("alpha:task", "t1"): "t1-src"})
        assert summary["status"] == "valid"
        assert len(project.list("alpha:log")) == 2

    def test_undeclared_type_aborts(self, project, source, site, tmp_path, cli):
        root = make_git_repo(tmp_path / "narrow")
        assert cli("init", "--schemas", "alpha", root=root).code == 0
        narrow = open_store(root)
        before = tree(narrow)
        with pytest.raises(MergeError, match="beta:plan") as caught:
            merge(narrow, source)
        assert "beta:review" in caught.value.details["unknown_types"]
        assert tree(narrow) == before

    def test_mapped_type_missing_from_target_aborts(self, project, source):
        with pytest.raises(MergeError, match="ghost:task"):
            merge(project, source, namespaces={"alpha": "ghost"})

    def test_source_must_be_a_store(self, project, tmp_path):
        with pytest.raises(MergeError, match="not a store"):
            merge_store(Store(project.store_path), project.schemas(), tmp_path)


def test_invalid_result_exits_with_validation_status(cli, project, source, monkeypatch):
    monkeypatch.setattr("canon.merge.validate_store", lambda *a, **k: ["boom"])
    result = cli("merge", str(source.store_path), "--format", "json")
    assert result.code == 4
    assert result.json["status"] == "invalid" and result.json["errors"] == ["boom"]
