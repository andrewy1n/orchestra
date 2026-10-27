from __future__ import annotations

import json

from canon.record_file import dump_record, load_record
from canon.revision import with_revision
from conftest import git, make_task


def rewrite(project, record, **changes):
    path = project.store_path / "records" / record["record_type"].replace(":", "__") / f"{record['id']}.md"
    loaded = load_record(path.read_text(), path)
    for key, value in changes.items():
        if value is None:
            loaded.pop(key, None)
        else:
            loaded[key] = value
    path.write_text(dump_record(with_revision(loaded)))
    return path


def test_valid_store_json(cli, project):
    make_task(project, "t")
    result = cli("validate", "--format", "json")
    assert result.code == 0
    assert result.json == {"status": "valid", "errors": [], "records": 1}


def test_valid_store_text(cli, project):
    make_task(project, "t")
    result = cli("validate", "--format", "text")
    assert result.code == 0
    assert result.out == "valid: 1 records\n"


def test_invalid_store_prints_the_error_list(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, payload={"title": "t", "bogus": 1})
    result = cli("validate", "--format", "json")
    assert result.code == 4
    body = result.json
    assert body["status"] == "invalid"
    assert body["errors"] == [f"{task['id']}: payload field 'bogus' is not declared by alpha:task"]
    text = cli("validate", "--format", "text")
    assert text.code == 4
    assert text.out.splitlines() == body["errors"]


def test_json_is_the_default_format(cli, project):
    assert cli("validate").json["status"] == "valid"


def test_errors_are_stable_across_runs(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, lifecycle_state="finished")
    assert cli("validate").json["errors"] == cli("validate").json["errors"]


def test_every_record_is_checked(cli, project):
    for subject in ("a", "b", "c"):
        rewrite(project, make_task(project, subject), payload={"title": 1})
    assert len(cli("validate").json["errors"]) == 3


def test_legacy_envelope_keys_are_reported(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, base_kind="commitment", identity="x")
    errors = cli("validate").json["errors"]
    assert errors == [f"{task['id']}: unknown envelope keys ['base_kind', 'identity']"]


def test_missing_envelope_keys_are_reported(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, recorded_at=None)
    assert "missing required fields ['recorded_at']" in cli("validate").json["errors"][0]


def test_unknown_record_type_is_reported(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, record_type="alpha:ghost")
    errors = project.validate()
    assert any("unknown record type 'alpha:ghost'" in e for e in errors)


def test_revision_tamper_is_reported(cli, project):
    task = make_task(project, "t")
    path = project.store_path / "records" / "alpha__task" / f"{task['id']}.md"
    path.write_text(path.read_text().replace('"t"', '"u"', 1))
    assert any("revision tamper" in e for e in cli("validate").json["errors"])


def test_two_active_current_records_for_one_subject_are_reported(cli, project):
    first = project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    project.supersede(first["id"])
    other = project.create(record_type="alpha:config", subject="api", payload={"title": "a", "level": 1})
    rewrite(project, other, subject="web")
    errors = cli("validate").json["errors"]
    assert any(f"multiple active alpha:config for subject='web'" in e for e in errors)


def test_superseded_record_without_a_successor_is_reported(cli, project):
    config = project.create(record_type="alpha:config", subject="web", payload={"title": "a", "level": 1})
    rewrite(project, config, lifecycle_state="superseded")
    errors = cli("validate").json["errors"]
    assert any("requires exactly one same-type successor, found 0" in e for e in errors)


def test_correction_chain_is_checked(cli, project):
    make_task(project, "t")
    log = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "a"})
    project.correct(log["id"], payload={"message": "b"})
    other = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "c"})
    rewrite(project, other, relationships={"corrects": [log["id"]]})
    errors = cli("validate").json["errors"]
    assert any("requires exactly one correcting successor, found 2" in e for e in errors)


def test_relationship_targets_must_exist_and_keys_are_limited(cli, project):
    task = make_task(project, "t")
    rewrite(project, task, relationships={"depends_on": ["rec-x"], "supersedes": ["rec-00000000-0000-0000-0000-000000000000"]})
    errors = cli("validate").json["errors"]
    assert any("unknown relationship 'depends_on'" in e for e in errors)
    assert any("unknown relationship target" in e for e in errors)


def test_history_snapshots_are_checked(cli, project):
    task = make_task(project, "t")
    project.update(task["id"], payload={"owner": "ann"})
    snapshot = next((project.store_path / "history" / "alpha__task").rglob("*.md"))
    assert cli("validate").code == 0
    snapshot.write_text(snapshot.read_text().replace('"t"', '"u"', 1))
    assert any("history tamper" in e for e in cli("validate").json["errors"])


def test_event_records_need_their_create_snapshot(cli, project):
    make_task(project, "t")
    project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "a"})
    snapshot = next((project.store_path / "history" / "alpha__log").rglob("*.md"))
    snapshot.unlink()
    assert any("missing create audit snapshot" in e for e in cli("validate").json["errors"])


def test_committed_records_cannot_be_edited_in_place(cli, project, repo):
    task = make_task(project, "t")
    git(repo, "add", "-A")
    assert git(repo, "commit", "-qm", "store").returncode == 0
    assert cli("validate").code == 0
    project.update(task["id"], payload={"owner": "ann"})
    assert cli("validate").code == 0
    path = project.store_path / "records" / "alpha__task" / f"{task['id']}.md"
    path.write_text(path.read_text().replace("planned", "done"))
    errors = cli("validate").json["errors"]
    assert any("immutability violation" in e for e in errors)


def test_config_and_snapshots_may_change_after_a_commit(cli, project, repo, site):
    import copy

    from conftest import ALPHA

    make_task(project, "t")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "store")
    bumped = copy.deepcopy(ALPHA)
    bumped["version"] = "0.2.0"
    site.publish(bumped)
    assert cli.ok("schemas", "sync")["status"] == "synced"
    assert cli("validate").code == 0
    assert json.loads((project.store_path / "config.json").read_text())["schemas"]["alpha"] == "0.2.0"


def test_stray_files_in_the_records_directory_are_reported(cli, project):
    make_task(project, "t")
    (project.store_path / "records" / "alpha__task" / "notes.txt").write_text("x")
    assert any("unrecognized record file" in e for e in cli("validate").json["errors"])
