from __future__ import annotations

import copy
import json
import os
import subprocess
import sys

import pytest
from conftest import ALPHA, BETA

from orchestra.canon import modules
from orchestra.canon.backend import open_backend
from orchestra.canon.modules import discover
from orchestra.canon.project import open_store
from orchestra.canon.schema import SchemaError
from orchestra.canon.types import JsonValue


def test_migration_validation_preserves_input_list() -> None:
    from orchestra.canon.schema import check_migrations

    migrations: list[JsonValue] = [{"from": "1", "to": "2"}]
    assert check_migrations(migrations, "module") is migrations


def test_reference_targets_preserve_unvalidated_items() -> None:
    from orchestra.canon.schema import ref_targets

    assert ref_targets({"ref": [1]}) == [1]


def test_unhashable_lifecycle_retains_type_error() -> None:
    from orchestra.canon.schema import validate_module

    with pytest.raises(TypeError):
        validate_module(
            {
                "namespace": "a",
                "version": "1.0.0",
                "types": {"t": {"purpose": "x", "lifecycle": [], "fields": {}}},
            }
        )


GAMMA_V1 = {
    "namespace": "gamma",
    "version": "1.0.0",
    "types": {
        "report": {
            "purpose": "Outcome of one run",
            "lifecycle": "event",
            "fields": {
                "status": {"enum": ["ok", "bad"]},
                "labels": {"list": {"type": "string"}, "optional": True},
            },
        },
        "note": {
            "purpose": "A current note",
            "lifecycle": "current",
            "fields": {"text": {"type": "string"}},
        },
    },
    "migrations": [],
}

GAMMA_V2 = {
    "namespace": "gamma",
    "version": "2.0.0",
    "types": {
        "execution-report": {
            "purpose": "Outcome of one run",
            "lifecycle": "event",
            "fields": {
                "result": {"enum": ["done", "bad"]},
                "labels": {"list": {"type": "string"}, "optional": True},
            },
        },
        "note": {
            "purpose": "A current note",
            "lifecycle": "current",
            "fields": {"body_text": {"type": "string"}},
        },
    },
    "migrations": [
        {
            "from": "1",
            "to": "2",
            "rename_type": {"gamma:report": "gamma:execution-report"},
            "rename_field": {
                "gamma:execution-report": {"status": "result"},
                "gamma:note": {"text": "body_text"},
            },
            "map_enum": {"gamma:execution-report.result": {"ok": "done"}},
        }
    ],
}


def test_discovery_finds_modules_through_entry_points(site):
    found = discover()
    assert set(found) == {"alpha", "beta"}
    assert found["alpha"].version == "0.1.0"
    assert found["alpha"].source == "canonfix_alpha.schemas/alpha.json"
    assert found["alpha"].module["types"]["task"]["lifecycle"] == "staged"


def test_discovery_with_faked_entry_points(monkeypatch, site):
    class Entry:
        name = "beta"
        value = "canonfix_beta.schemas"

    monkeypatch.setattr(modules, "_entry_points", lambda: [Entry()])
    assert set(discover()) == {"beta"}


def test_discovery_refuses_an_entry_point_that_names_an_object(monkeypatch, site):
    class Entry:
        name = "beta"
        value = "canonfix_beta:schemas/beta.json"

    monkeypatch.setattr(modules, "_entry_points", lambda: [Entry()])
    with pytest.raises(SchemaError, match="must name a package"):
        discover()


def test_discovery_reads_module_files_named_in_canon_schema_path(monkeypatch, site, tmp_path):
    gamma = tmp_path / "gamma.json"
    gamma.write_text(json.dumps(GAMMA_V1))
    monkeypatch.setenv("CANON_SCHEMA_PATH", f"{gamma}{os.pathsep}")
    found = discover()
    assert set(found) == {"alpha", "beta", "gamma"}
    assert found["gamma"].source == str(gamma)


def test_canon_schema_path_overrides_an_installed_module_of_the_same_namespace(
    monkeypatch, site, tmp_path
):
    trimmed = copy.deepcopy(ALPHA)
    del trimmed["types"]["log"]
    path = tmp_path / "alpha.json"
    path.write_text(json.dumps(trimmed))
    monkeypatch.setenv("CANON_SCHEMA_PATH", str(path))
    found = discover()
    assert found["alpha"].source == str(path)
    assert "log" not in found["alpha"].module["types"]


def test_discovery_refuses_one_namespace_twice_in_canon_schema_path(monkeypatch, site, tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    first.write_text(json.dumps(GAMMA_V1))
    second.write_text(json.dumps(GAMMA_V2))
    monkeypatch.setenv("CANON_SCHEMA_PATH", f"{first}{os.pathsep}{second}")
    with pytest.raises(SchemaError, match="provided twice"):
        discover()


def test_discovery_refuses_an_unreadable_canon_schema_path(monkeypatch, site, tmp_path):
    monkeypatch.setenv("CANON_SCHEMA_PATH", str(tmp_path / "missing.json"))
    with pytest.raises(SchemaError, match="CANON_SCHEMA_PATH"):
        discover()


def test_discovery_refuses_one_namespace_from_two_packages(site):
    other = copy.deepcopy(ALPHA)
    other["version"] = "0.2.0"
    site.publish(other, package="canonfix_alpha_again")
    with pytest.raises(SchemaError, match="provided twice"):
        discover()


def test_discovery_refuses_an_invalid_module(site):
    broken = copy.deepcopy(ALPHA)
    broken["types"]["task"]["lifecycle"] = "cyclic"
    site.publish(broken)
    with pytest.raises(SchemaError, match="lifecycle"):
        discover()


def test_discovery_in_a_fresh_interpreter(site, repo):
    env = site.env()

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "orchestra.canon", "--root", str(repo), *args],
            capture_output=True,
            text=True,
            env=env,
        )

    result = run("init", "--schemas", "alpha,beta")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["schemas"] == {"alpha": "0.1.0", "beta": "0.1.0"}
    created = run("create", "--type", "alpha:task", "--subject", "t", "--payload", '{"title": "x"}')
    assert created.returncode == 0, created.stdout
    assert json.loads(run("validate").stdout)["status"] == "valid"


def test_init_creates_config_and_snapshots(cli, repo):
    result = cli.ok("init", "--schemas", "alpha,beta")
    assert result["status"] == "initialized"
    store = repo / ".canon"
    config = json.loads((store / "config.json").read_text())
    assert config == {
        "format": "canon/1",
        "schemas": {"alpha": "0.1.0", "beta": "0.1.0"},
        "settings": {},
        "backend": "sqlite",
    }
    assert json.loads((store / "schemas" / "alpha.json").read_text()) == ALPHA
    assert json.loads((store / "schemas" / "beta.json").read_text()) == BETA
    assert not (store / "meta.json").exists()
    assert not (store / ".write.lock").exists()


def test_init_without_schemas_makes_an_empty_store(cli, repo):
    cli.ok("init")
    assert json.loads((repo / ".canon" / "config.json").read_text())["schemas"] == {}
    assert cli.ok("validate")["status"] == "valid"


def test_init_with_an_uninstalled_namespace_creates_nothing(cli, repo):
    result = cli("init", "--schemas", "alpha,missing")
    assert result.code == 4
    assert result.json["error"] == "schema"
    assert "missing" in result.json["message"]
    assert not (repo / ".canon").exists()


def test_init_is_idempotent_and_refuses_new_namespaces(cli):
    cli.ok("init", "--schemas", "alpha")
    assert cli.ok("init", "--schemas", "alpha")["status"] == "already_initialized"
    result = cli("init", "--schemas", "alpha,beta")
    assert result.code == 1
    assert "schemas add" in result.json["message"]


def test_init_needs_a_git_repository(cli, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    result = cli("init", "--schemas", "alpha", root=plain)
    assert result.code == 1
    assert result.json["error"] == "git_context"


def test_schemas_add_installs_a_namespace(cli, repo):
    cli.ok("init", "--schemas", "alpha")
    result = cli.ok("schemas", "add", "beta")
    assert result["schemas"]["beta"] == {"from": None, "to": "0.1.0", "action": "copied"}
    config = json.loads((repo / ".canon" / "config.json").read_text())
    assert config["schemas"] == {"alpha": "0.1.0", "beta": "0.1.0"}
    assert (repo / ".canon" / "schemas" / "beta.json").is_file()
    again = cli.ok("schemas", "add", "beta")
    assert again["schemas"]["beta"]["action"] == "unchanged"


def test_schemas_add_refuses_an_uninstalled_namespace(cli, repo):
    cli.ok("init", "--schemas", "alpha")
    result = cli("schemas", "add", "nope")
    assert result.code == 4
    assert "nope" in result.json["message"]
    config = json.loads((repo / ".canon" / "config.json").read_text())
    assert config["schemas"] == {"alpha": "0.1.0"}


def test_sync_copies_a_missing_snapshot(cli, repo):
    cli.ok("init", "--schemas", "alpha,beta")
    (repo / ".canon" / "schemas" / "beta.json").unlink()
    result = cli.ok("schemas", "sync")
    assert result["schemas"]["beta"]["action"] == "copied"
    assert result["status"] == "synced"


def test_sync_without_changes_is_a_no_op(cli):
    cli.ok("init", "--schemas", "alpha,beta")
    result = cli.ok("schemas", "sync")
    assert {v["action"] for v in result["schemas"].values()} == {"unchanged"}
    assert result["migrated_records"] == 0


def test_sync_minor_bump_updates_the_snapshot_and_keeps_records_valid(cli, site, repo):
    cli.ok("init", "--schemas", "alpha,beta")
    cli.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')
    bumped = copy.deepcopy(ALPHA)
    bumped["version"] = "0.2.0"
    bumped["types"]["task"]["fields"]["estimate"] = {"type": "integer", "optional": True}
    bumped["types"]["extra"] = {"purpose": "New type", "lifecycle": "event", "fields": {}}
    site.publish(bumped)
    result = cli.ok("schemas", "sync")
    assert result["schemas"]["alpha"] == {"from": "0.1.0", "to": "0.2.0", "action": "updated"}
    assert result["schemas"]["beta"]["action"] == "unchanged"
    assert result["errors"] == []
    config = json.loads((repo / ".canon" / "config.json").read_text())
    assert config["schemas"]["alpha"] == "0.2.0"
    snapshot = json.loads((repo / ".canon" / "schemas" / "alpha.json").read_text())
    assert snapshot["version"] == "0.2.0"
    cli.ok(
        "create",
        "--type",
        "alpha:task",
        "--subject",
        "t2",
        "--set",
        "title=y",
        "--set",
        "estimate=3",
    )
    assert cli.ok("validate")["status"] == "valid"


def test_sync_refuses_a_downgrade(cli, site):
    cli.ok("init", "--schemas", "alpha")
    older = copy.deepcopy(ALPHA)
    older["version"] = "0.0.9"
    site.publish(older)
    result = cli("schemas", "sync")
    assert result.code == 4
    assert "older" in result.json["message"]


def test_sync_refuses_a_namespace_that_is_no_longer_installed(cli, site):
    cli.ok("init", "--schemas", "alpha,beta")
    (site.root / "canonfix_beta-0.1.dist-info" / "entry_points.txt").write_text("")
    result = cli("schemas", "sync")
    assert result.code == 4
    assert "beta" in result.json["message"]


def test_sync_reports_records_that_the_new_version_breaks(cli, site):
    cli.ok("init", "--schemas", "alpha,beta")
    cli.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')
    breaking = copy.deepcopy(ALPHA)
    breaking["version"] = "0.2.0"
    breaking["types"]["task"]["fields"]["estimate"] = {"type": "integer"}
    site.publish(breaking)
    result = cli("schemas", "sync")
    assert result.code == 4
    assert result.json["status"] == "invalid"
    assert any("missing payload field 'estimate'" in e for e in result.json["errors"])


class TestMigration:
    @pytest.fixture
    def migrating(self, cli, site, repo):
        site.publish(copy.deepcopy(GAMMA_V1))
        cli.ok("init", "--schemas", "gamma")
        project = open_store(repo)
        report = project.create(
            record_type="gamma:report", subject="run-1", payload={"status": "ok", "labels": ["a"]}
        )
        bad = project.create(record_type="gamma:report", subject="run-2", payload={"status": "bad"})
        note = project.create(record_type="gamma:note", subject="n", payload={"text": "first"})
        newer = project.supersede(note["id"], payload={"text": "second"})
        return project, report, bad, newer["record"]

    def test_major_bump_runs_the_declared_migration(self, cli, site, repo, migrating):
        project, report, bad, note = migrating
        site.publish(copy.deepcopy(GAMMA_V2))
        result = cli.ok("schemas", "sync")
        assert result["schemas"]["gamma"] == {"from": "1.0.0", "to": "2.0.0", "action": "migrated"}
        assert result["errors"] == []
        assert result["migrated_records"] == 4
        project = open_store(repo)
        moved = project.get(report["id"])
        assert moved["record_type"] == "gamma:execution-report"
        assert moved["payload"] == {"result": "done", "labels": ["a"]}
        assert project.get(bad["id"])["payload"] == {"result": "bad"}
        assert project.get(note["id"])["payload"] == {"body_text": "second"}
        assert [r["id"] for r in project.list("gamma:execution-report")].count(report["id"]) == 1
        assert project.list("gamma:execution-report").__len__() == 2
        assert not open_backend(project.store_path).record_exists("gamma:report", report["id"])
        assert project.validate() == []

    def test_migration_rewrites_history_snapshots(self, cli, site, repo, migrating):
        site.publish(copy.deepcopy(GAMMA_V2))
        cli.ok("schemas", "sync")
        history = list(open_backend(repo / ".canon").read_history())
        assert not any(record["record_type"] == "gamma:report" for record in history)
        assert (
            len([record for record in history if record["record_type"] == "gamma:execution-report"])
            == 2
        )
        note_snapshots = [record for record in history if record["record_type"] == "gamma:note"]
        assert note_snapshots
        assert all("body_text" in record["payload"] for record in note_snapshots)

    def test_migration_is_idempotent(self, cli, site, migrating):
        site.publish(copy.deepcopy(GAMMA_V2))
        cli.ok("schemas", "sync")
        again = cli.ok("schemas", "sync")
        assert again["schemas"]["gamma"]["action"] == "unchanged"
        assert again["migrated_records"] == 0

    def test_major_bump_without_a_migration_is_refused(self, cli, site, repo, migrating):
        bare = copy.deepcopy(GAMMA_V2)
        bare["migrations"] = []
        site.publish(bare)
        result = cli("schemas", "sync")
        assert result.code == 4
        assert "no migration" in result.json["message"]
        config = json.loads((repo / ".canon" / "config.json").read_text())
        assert config["schemas"]["gamma"] == "1.0.0"

    def test_migration_chains_across_several_majors(self, cli, site, repo, migrating):
        _, report, *_ = migrating
        v3 = copy.deepcopy(GAMMA_V2)
        v3["version"] = "3.0.0"
        v3["types"]["execution-report"]["fields"]["result"] = {"enum": ["finished", "bad"]}
        v3["migrations"].append(
            {
                "from": "2",
                "to": "3",
                "map_enum": {"gamma:execution-report.result": {"done": "finished"}},
            }
        )
        site.publish(v3)
        result = cli.ok("schemas", "sync")
        assert result["errors"] == []
        assert open_store(repo).get(report["id"])["payload"]["result"] == "finished"


def test_validation_uses_snapshots_not_installed_packages(cli, site, repo):
    cli.ok("init", "--schemas", "alpha,beta")
    cli.ok("create", "--type", "alpha:task", "--subject", "t", "--set", 'title="x"')
    for package in site.packages:
        sys.modules.pop(package, None)
    for dist in site.root.glob("*.dist-info"):
        (dist / "entry_points.txt").write_text("")
    assert cli.ok("validate")["status"] == "valid"
    assert cli.ok("list", "--type", "task")["count"] == 1


def test_a_snapshot_that_disagrees_with_config_is_refused(cli, repo):
    cli.ok("init", "--schemas", "alpha")
    path = repo / ".canon" / "schemas" / "alpha.json"
    data = json.loads(path.read_text())
    data["version"] = "0.9.0"
    path.write_text(json.dumps(data))
    result = cli("validate")
    assert result.code == 4
    assert "config.json pins 0.1.0" in result.json["message"]


def test_schemas_show(cli):
    cli.ok("init", "--schemas", "alpha,beta")
    overview = cli.ok("schemas", "show")["schemas"]
    assert overview["alpha"]["version"] == "0.1.0"
    assert overview["alpha"]["types"]["task"] == {
        "purpose": "A unit of work",
        "lifecycle": "staged",
    }
    assert cli.ok("schemas", "show", "beta") == BETA
    one = cli.ok("schemas", "show", "--type", "review")
    assert one["record_type"] == "beta:review"
    assert one["fields"]["verdict"] == {"enum": ["pass", "fail"]}
    task = cli.ok("schemas", "show", "--type", "alpha:task")
    assert "depends_on" in task["fields"]
    assert task["transitions"]["planned"] == ["in_progress", "withdrawn", "superseded"]
    assert cli("schemas", "show", "nope").code == 4
