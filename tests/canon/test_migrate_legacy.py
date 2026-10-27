from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from canon.legacy import LegacyError, migrate_store
from canon.project import open_store
from conftest import make_git_repo

_DEFAULT_MODULES = os.pathsep.join(
    str(Path.home() / rel)
    for rel in (
        "orchestra/orchestra/schemas/plan.json",
        "orchestra/orchestra/schemas/run.json",
        "affidavit/affidavit/schemas/aff.json",
    )
)
MODULES = os.environ.get("CANON_TEST_SCHEMAS", _DEFAULT_MODULES)

pytestmark = pytest.mark.skipif(
    not all(Path(p).is_file() for p in MODULES.split(os.pathsep)),
    reason="needs the plan, run and aff modules (set CANON_TEST_SCHEMAS)",
)

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"


def old_record(rid, record_type, subject, state, payload, body="", relationships=None):
    return {
        "base_kind": "x",
        "id": rid,
        "identity": "unknown",
        "lifecycle_state": state,
        "payload": payload,
        "record_type": f"project:{record_type}",
        "recorded_at": "2026-10-01T00:00:00+00:00",
        "relationships": relationships or {},
        "revision": "sha256:old",
        "stewardship": {"steward": "agent"},
        "subject": subject,
        "body": body,
    }


def write_old(store: Path, record: dict) -> None:
    body = record.pop("body")
    path = store / "records" / record["record_type"].replace(":", "__") / f"{record['id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{json.dumps(record, indent=2)}\n---\n\n{body}")


def legacy_store(root: Path, *, effort: str = "loop") -> Path:
    store = root / ".artifacts"
    store.mkdir()
    (store / "meta.json").write_text("{}")
    (store / "project-design.json").write_text(
        json.dumps({"phase_gate": {"suite": {"mode": "full", "command": "pytest", "gate": "advisory"}}})
    )
    (store / "views").mkdir()
    (store / "views" / "handoff.md").write_text("old view")
    eff = "rec-00000000-0000-4000-8000-000000000001"
    phase = "rec-00000000-0000-4000-8000-000000000002"
    first = "rec-00000000-0000-4000-8000-000000000003"
    second = "rec-00000000-0000-4000-8000-000000000004"
    acc = "rec-00000000-0000-4000-8000-000000000005"
    run = "rec-00000000-0000-4000-8000-000000000006"
    task = {"phase": "p1", "kind": "deliver", "assignee": "", "effort": effort, "decisions": "", "requirements": "R1, R2"}
    for record in (
        old_record(eff, "active-goal", "loop", "active", {"goal": "g", "kind": "deliver", "scope": "effort"}),
        old_record(phase, "phase", "p1", "in_progress", {"title": "P", "ordinal": 1, "effort": "loop"}, PHASE_BODY),
        old_record(first, "work-item", "a", "done", {"title": "A", **task}, "## Description\n\nd\n"),
        old_record(second, "work-item", "b", "planned", {"title": "B", **task}, "## Description\n\nd\n", {"depends_on": [first]}),
        old_record(acc, "acceptance", "a", "active", {"method": "tdd", "phase": "p1", "effort": "loop", "verify_command": "pytest", "test_ids": "t::a,t::b"}),
        old_record(run, "check-run", "a", "recorded", {"criterion_id": acc, "revision": "abc", "result": "pass", "effort": "loop", "method": "tdd", "signed_by": "", "failing_node_ids": "[]"}, relationships={"informed_by": [acc]}),
    ):
        write_old(store, record)
    return store


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    monkeypatch.setenv("CANON_SCHEMA_PATH", MODULES)
    return make_git_repo(tmp_path / "work")


def test_migrate_rebuilds_a_legacy_store_in_place(legacy):
    store = legacy_store(legacy)
    report = migrate_store(store, ["plan", "run", "aff"])
    assert report["status"] == "migrated" and report["errors"] == []
    assert sorted(p.name for p in store.iterdir()) == ["config.json", "history", "log", "records", "schemas"]
    project = open_store(legacy)
    assert len(project.records()) == 6
    second = project.resolve("plan:work-item", "b")
    assert second["payload"]["depends_on"] == ["a"]
    assert second["payload"]["requirements"] == ["R1", "R2"]
    assert project.derived()[second["id"]]["ready"] is True
    check = project.resolve("aff:check-run", "a")
    assert check["payload"]["informed_by"] == [project.resolve("plan:acceptance", "a")["id"]]
    assert check["payload"]["failing_node_ids"] == []
    assert "scope" not in project.resolve("plan:effort", "loop")["payload"]
    config = json.loads((store / "config.json").read_text())
    assert config["settings"]["run"]["phase_gate"]["suite"]["gate"] == "advisory"
    assert project.validate() == []


def test_migrate_leaves_the_store_untouched_when_validation_fails(legacy):
    store = legacy_store(legacy, effort="missing")
    before = sorted(p.name for p in store.iterdir())
    report = migrate_store(store, ["plan", "run", "aff"])
    assert report["status"] == "invalid"
    assert any("missing" in error for error in report["errors"])
    assert sorted(p.name for p in store.iterdir()) == before
    assert not (store.parent / ".artifacts.canon-staging").exists()


def test_migrate_with_allow_errors_replaces_the_store_and_reports(legacy):
    store = legacy_store(legacy, effort="missing")
    report = migrate_store(store, ["plan", "run", "aff"], allow_errors=True)
    assert report["status"] == "migrated_with_errors"
    assert (store / "config.json").is_file() and not (store / "meta.json").exists()


def test_migrate_refuses_a_store_with_record_files_it_cannot_read(legacy):
    store = legacy_store(legacy)
    stray = store / "records" / "project__current-position" / "rec-old.json"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text("{}")
    with pytest.raises(LegacyError, match="cannot read"):
        migrate_store(store, ["plan", "run", "aff"])
    assert stray.is_file() and (store / "meta.json").is_file()


def test_migrate_refuses_a_canon_store(legacy):
    store = legacy_store(legacy)
    migrate_store(store, ["plan", "run", "aff"])
    with pytest.raises(LegacyError, match="already a canon store"):
        migrate_store(store, ["plan", "run", "aff"])
