from __future__ import annotations

import json

import pytest

from orchestra.canon import cli as canon_cli
from conftest import PLAN_BODY, make_task


@pytest.fixture
def ready(cli, project):
    return cli


def test_create_get_roundtrip(ready):
    created = ready.ok(
        "create", "--type", "alpha:task", "--subject", "t", "--payload", '{"title": "x"}'
    )
    assert created["ok"] and created["op"] == "create"
    record = created["record"]
    assert record["lifecycle_state"] == "planned"
    assert ready.ok("get", "--id", record["id"]) == record
    assert ready.ok("get", "--id", record["id"], "--type", "task") == record
    assert ready.ok("get", "--id", record["id"], "--field", "payload.title") == "x"


def test_set_values_are_json_decoded_and_merge_over_payload_file(ready, tmp_path):
    path = tmp_path / "payload.json"
    path.write_text(json.dumps({"title": "a", "level": 1}))
    record = ready.ok(
        "create",
        "--type",
        "config",
        "--subject",
        "c",
        "--payload-file",
        str(path),
        "--set",
        "level=2",
        "--set",
        "enabled=true",
        "--set",
        'tags=["x", "y"]',
        "-p",
        "ratio=0.5",
    )["record"]
    assert record["payload"] == {
        "title": "a",
        "level": 2,
        "enabled": True,
        "tags": ["x", "y"],
        "ratio": 0.5,
    }


def test_create_requires_a_subject(ready):
    with pytest.raises(SystemExit) as caught:
        ready("create", "--type", "alpha:task")
    assert caught.value.code == 2


def test_validation_failure_is_a_json_error_with_exit_4(ready):
    result = ready("create", "--type", "alpha:task", "--subject", "t", "--payload", '{"nope": 1}')
    assert result.code == 4
    assert result.json["error"] == "validation"
    assert "'nope' is not declared" in result.json["message"]


def test_unknown_and_ambiguous_types(ready, site):
    result = ready("create", "--type", "alpha:ghost", "--subject", "t", "--payload", "{}")
    assert result.code == 4 and result.json["error"] == "unknown_type"
    import copy

    from conftest import BETA

    other = copy.deepcopy(BETA)
    other["types"]["task"] = {"purpose": "p", "lifecycle": "event", "fields": {}}
    site.publish(other)
    ready.ok("schemas", "sync")
    result = ready("create", "--type", "task", "--subject", "t", "--payload", "{}")
    assert result.json["error"] == "ambiguous_type"


def test_body_flags(ready, tmp_path):
    inline = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )
    assert inline["record"]["body"] == PLAN_BODY
    path = tmp_path / "body.md"
    path.write_text("## Orientation\n\nfrom file\n")
    from_file = ready.ok(
        "create",
        "--type",
        "beta:plan",
        "--subject",
        "p2",
        "--set",
        'goal="g"',
        "--body-file",
        str(path),
    )
    assert from_file["record"]["body"] == "## Orientation\n\nfrom file\n"
    both = ready(
        "create", "--type", "beta:plan", "--subject", "p3", "--body", "x", "--body-file", str(path)
    )
    assert both.json["error"] == "invalid_body"
    missing = ready(
        "create", "--type", "beta:plan", "--subject", "p4", "--body-file", str(tmp_path / "nope")
    )
    assert missing.json["error"] == "invalid_body"


def test_get_body_only(ready):
    record = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )["record"]
    result = ready("get", "--id", record["id"], "--body-only")
    assert result.out == PLAN_BODY + "\n"


def test_get_errors(ready):
    task = ready.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')[
        "record"
    ]
    missing = ready("get", "--id", "rec-00000000-0000-0000-0000-000000000000")
    assert missing.code == 1 and missing.json["error"] == "not_found"
    wrong = ready("get", "--id", task["id"], "--type", "alpha:log")
    assert wrong.json["error"] == "wrong_type"
    assert wrong.json["actual_type"] == "alpha:task"
    assert (
        ready("get", "--id", task["id"], "--field", "payload.zzz").json["error"]
        == "field_not_found"
    )


def test_update_by_id_and_by_type_and_subject(ready):
    task = ready.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')[
        "record"
    ]
    moved = ready.ok("update", "--id", task["id"], "--transition", "in_progress")["record"]
    assert moved["lifecycle_state"] == "in_progress"
    patched = ready.ok("update", "--type", "task", "--subject", "t", "--set", 'owner="ann"')[
        "record"
    ]
    assert patched["lifecycle_state"] == "in_progress"
    assert patched["payload"]["owner"] == "ann"
    assert patched["id"] == task["id"]


def test_update_without_target_is_missing_target(ready):
    result = ready("update", "--set", 'owner="ann"')
    assert result.code == 1 and result.json["error"] == "missing_target"
    unknown = ready("update", "--type", "task", "--subject", "ghost")
    assert unknown.json["error"] == "not_found"


def test_refused_transition_exits_3(ready):
    task = ready.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')[
        "record"
    ]
    result = ready("update", "--id", task["id"], "--transition", "done")
    assert result.code == 3 and result.json["error"] == "invalid_transition"
    result = ready("update", "--id", task["id"], "--transition", "superseded")
    assert result.code == 3 and result.json["error"] == "use_supersede"


def test_event_update_is_append_only(ready, project):
    make_task(project, "t")
    log = ready.ok(
        "create", "--type", "log", "--subject", "t", "--payload", '{"task": "t", "message": "m"}'
    )["record"]
    result = ready("update", "--id", log["id"], "--set", 'message="n"')
    assert result.code == 3 and result.json["error"] == "append_only"


def test_body_is_kept_replaced_or_cleared_on_update(ready):
    plan = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )["record"]
    kept = ready.ok("update", "--id", plan["id"], "--set", 'goal="h"')["record"]
    assert kept["body"] == PLAN_BODY
    replaced = ready.ok("update", "--id", plan["id"], "--body", "## Orientation\n\nnew\n")["record"]
    assert replaced["body"] == "## Orientation\n\nnew\n"
    refused = ready("update", "--id", plan["id"], "--body", "")
    assert refused.json["error"] == "validation"


def test_supersede_carries_body_and_payload_forward(ready):
    plan = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )["record"]
    result = ready.ok("supersede", "--type", "plan", "--subject", "p", "--set", 'goal="h"')
    assert result["record"]["body"] == PLAN_BODY
    assert result["record"]["payload"] == {"goal": "h"}
    assert result["predecessor"]["id"] == plan["id"]
    assert result["predecessor"]["lifecycle_state"] == "superseded"
    replaced = ready.ok(
        "supersede", "--id", result["record"]["id"], "--body", "## Orientation\n\nz\n"
    )
    assert replaced["record"]["body"] == "## Orientation\n\nz\n"


def test_correct_event(ready, project):
    make_task(project, "t")
    log = ready.ok(
        "create", "--type", "log", "--subject", "t", "--payload", '{"task": "t", "message": "m"}'
    )["record"]
    result = ready.ok("correct", "--id", log["id"], "--set", 'message="n"')
    assert result["record"]["relationships"] == {"corrects": [log["id"]]}
    again = ready("correct", "--id", log["id"])
    assert again.code == 4 and "already corrected" in again.json["message"]
    not_event = ready("correct", "--type", "task", "--subject", "t")
    assert not_event.json["error"] == "not_correctable"


def test_expected_revision(ready):
    task = ready.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')[
        "record"
    ]
    stale = ready(
        "update",
        "--id",
        task["id"],
        "--set",
        'owner="ann"',
        "--expected-revision",
        "sha256:" + "0" * 64,
    )
    assert stale.code == 2 and stale.json["error"] == "stale_write"
    exact = ready.ok(
        "update",
        "--id",
        task["id"],
        "--set",
        'owner="ann"',
        "--expected-revision",
        task["revision"],
    )
    assert exact["record"]["revision"] != task["revision"]
    current = ready.ok(
        "update", "--id", task["id"], "--set", 'owner="bob"', "--expected-revision", "@current"
    )
    assert current["record"]["payload"]["owner"] == "bob"
    outdated = ready("supersede", "--id", task["id"], "--expected-revision", task["revision"])
    assert outdated.code == 2
    assert ready.ok("get", "--id", task["id"])["lifecycle_state"] == "planned"


def test_every_write_command_reports_the_store_it_wrote_to(ready, project):
    store = str(project.store_path)
    task = ready.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')
    assert task["store"] == store
    assert (
        ready.ok("update", "--id", task["record"]["id"], "--set", 'owner="ann"')["store"] == store
    )
    assert ready.ok("supersede", "--type", "task", "--subject", "t")["store"] == store
    log = ready.ok(
        "create", "--type", "log", "--subject", "t", "--payload", '{"task": "t", "message": "m"}'
    )
    assert (
        ready.ok("correct", "--id", log["record"]["id"], "--set", 'message="n"')["store"] == store
    )
    op = json.dumps(
        {"op": "create", "type": "alpha:task", "subject": "a", "payload": {"title": "a"}}
    )
    assert ready.ok("apply", stdin=op)["store"] == store


def test_correct_with_stale_revision(ready, project):
    make_task(project, "t")
    log = ready.ok(
        "create", "--type", "log", "--subject", "t", "--payload", '{"task": "t", "message": "m"}'
    )["record"]
    stale = ready("correct", "--id", log["id"], "--expected-revision", "sha256:" + "1" * 64)
    assert stale.code == 2 and stale.json["error"] == "stale_write"
    assert ready.ok("correct", "--id", log["id"], "--expected-revision", "@current")


def test_apply_runs_every_operation_and_reports_each_line(ready):
    ndjson = "\n".join(
        [
            json.dumps(
                {"op": "create", "type": "alpha:task", "subject": "a", "payload": {"title": "a"}}
            ),
            json.dumps(
                {
                    "op": "create",
                    "type": "alpha:task",
                    "subject": "b",
                    "payload": {"title": "b", "depends_on": ["a"]},
                }
            ),
            "",
            "not json",
            json.dumps(
                {
                    "op": "create",
                    "type": "alpha:task",
                    "subject": "c",
                    "payload": {"title": "c", "depends_on": ["zzz"]},
                }
            ),
            json.dumps({"op": "frobnicate"}),
            json.dumps(
                {
                    "op": "create",
                    "type": "alpha:task",
                    "subject": "d",
                    "payload": {"title": "d"},
                    "rels": {"x": ["y"]},
                }
            ),
            json.dumps([1]),
            json.dumps(
                {"op": "create", "type": "alpha:task", "subject": "e", "payload": {"title": "e"}}
            ),
        ]
    )
    result = ready("apply", stdin=ndjson + "\n")
    out = result.json
    assert result.code == 1
    assert (out["applied"], out["failed"]) == (3, 5)
    assert [r["line"] for r in out["results"]] == [1, 2, 4, 5, 6, 7, 8, 9]
    assert [r["ok"] for r in out["results"]] == [
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        True,
    ]
    assert out["results"][2]["error"] == "json"
    assert out["results"][3]["error"] == "validation"
    assert out["results"][4]["error"] == "unknown_op"
    assert "rels" in out["results"][5]["message"]
    assert ready.ok("list", "--type", "task")["count"] == 3


def test_apply_update_supersede_correct_by_id(ready, project):
    make_task(project, "t")
    log = project.create(
        record_type="alpha:log", subject="t", payload={"task": "t", "message": "m"}
    )
    task = project.resolve("task", "t")
    ndjson = "\n".join(
        json.dumps(op)
        for op in [
            {"op": "update", "id": task["id"], "transition": "in_progress"},
            {
                "op": "update",
                "id": task["id"],
                "payload": {"owner": "ann"},
                "expected_revision": "@current",
            },
            {"op": "correct", "id": log["id"], "payload": {"message": "n"}},
            {"op": "supersede", "id": task["id"]},
        ]
    )
    out = ready("apply", "--file", "-", stdin=ndjson).json
    assert out["ok"], out
    kinds = [r["op"] for r in out["results"]]
    assert kinds == ["update", "update", "correct", "supersede"]


def test_apply_reads_a_file(ready, tmp_path):
    path = tmp_path / "ops.ndjson"
    path.write_text(
        json.dumps(
            {"op": "create", "type": "alpha:task", "subject": "a", "payload": {"title": "a"}}
        )
        + "\n"
    )
    assert ready.ok("apply", str(path))["applied"] == 1
    path.write_text(
        json.dumps(
            {"op": "create", "type": "alpha:task", "subject": "b", "payload": {"title": "b"}}
        )
        + "\n"
    )
    assert ready.ok("apply", "--file", str(path))["applied"] == 1


def test_mutating_commands_are_refused_in_read_only_mode(cli, repo, project, monkeypatch):
    task = make_task(project, "t")
    commands = [
        ("init",),
        ("create", "--type", "alpha:task", "--subject", "x"),
        ("update", "--id", task["id"]),
        ("supersede", "--id", task["id"]),
        ("correct", "--id", task["id"]),
        ("apply",),
        ("schemas", "sync"),
        ("schemas", "add", "alpha"),
        ("merge", "somewhere"),
        ("import", "somewhere"),
    ]
    for command in commands:
        flagged = cli("--read-only", *command, stdin="")
        assert flagged.code == 1 and flagged.json["error"] == "read_only", command
    monkeypatch.setenv("CANON_READONLY", "1")
    for command in commands:
        assert cli(*command, stdin="").json["error"] == "read_only", command
    assert cli("get", "--id", task["id"]).code == 0
    assert cli("list").code == 0
    assert cli("validate").code == 0
    assert cli("schemas", "show").code == 0
    assert project.list("task")[0]["revision"] == task["revision"]


def test_the_declared_mutating_commands_cover_every_writing_subcommand():
    parser = canon_cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    commands = set(sub.choices)
    assert commands == {
        "init",
        "create",
        "update",
        "supersede",
        "correct",
        "apply",
        "get",
        "list",
        "validate",
        "schemas",
        "merge",
        "backup",
        "import",
        "export",
    }
    assert canon_cli.MUTATING_COMMANDS == {
        "init",
        "create",
        "update",
        "supersede",
        "correct",
        "apply",
        "merge",
        "import",
    }


def test_commands_report_a_missing_store(cli, repo):
    result = cli("list")
    assert result.code == 1
    assert result.json["error"] == "store_not_ready"


def test_store_flag_selects_a_store(cli, repo, tmp_path):
    from orchestra.canon.backend import open_backend

    other = tmp_path / "elsewhere"
    assert cli("--store", str(other), "init", "--schemas", "alpha").code == 0
    created = cli(
        "--store",
        str(other),
        "create",
        "--type",
        "alpha:task",
        "--subject",
        "t",
        "--set",
        'title="x"',
    )
    assert created.code == 0
    assert [record["subject"] for record in open_backend(other).list_records("alpha:task")] == ["t"]
