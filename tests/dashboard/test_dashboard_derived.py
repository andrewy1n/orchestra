"""Dashboard readers derive status, progress, release and assignment from records."""

from __future__ import annotations

import json
import shutil
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import helpers as h
import pytest
from conftest import REPO_ROOT, SCHEMA_FILES, build_store, run_cli

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend import journal as journal_mod
from dashboard.backend import phase as phase_mod
from dashboard.backend import snapshot as snapshot_mod
from dashboard.backend import task as task_mod
from orchestra.canon.project import open_store

EFFORT = "alpha"
PHASE = "p-one"


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    paths: list[str] = []
    for source in SCHEMA_FILES:
        module = json.loads(source.read_text())
        if source.name == "score.json":
            module["types"]["work-item"]["fields"]["write_root"] = {
                "type": "string",
                "optional": True,
            }
        target = tmp_path / source.name
        target.write_text(json.dumps(module))
        paths.append(str(target))
    monkeypatch.setenv("CANON_SCHEMA_PATH", ":".join(paths))
    root = build_store()
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def cli(store: Path):
    def run(*args: str):
        return run_cli(*args, root=store)

    return run


@pytest.fixture()
def defs(store: Path) -> dict[str, dict]:
    return h.schema_defs()


def _record(
    cli, defs, record_type: str, subject: str, payload: dict[str, object], body: str | None = None
) -> dict:
    h.ensure_refs(cli, defs, defs[record_type], payload)
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    body = body if body is not None else h.generic_body(defs[record_type])
    if body:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def _seed_phase(cli, defs) -> None:
    h.create_generic_record(
        cli,
        defs,
        "score:effort",
        subject=EFFORT,
        extra_payload={"goal": "ship alpha", "kind": "deliver"},
    )
    phase = h.create_generic_record(
        cli,
        defs,
        "score:phase",
        subject=PHASE,
        extra_payload={"title": "one", "ordinal": 1, "effort": EFFORT},
    )
    h.transition(cli, "score:phase", phase, "in_progress")


def _work_item(cli, defs, subject: str, *states: str, **fields: object) -> dict:
    payload: dict[str, object] = {
        "title": subject,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
        **fields,
    }
    record = _record(cli, defs, "score:work-item", subject, payload)
    if states:
        record = h.transition(cli, "score:work-item", record, *states)
    return record


def _spec(cli, defs, *requirements: str) -> dict:
    lines = "\n".join(f"{r}: text of {r}" for r in requirements)
    sections = defs["score:specification"].get("required_sections") or []
    body = "\n\n".join(
        f"## {name}\n\n{lines if name == 'Requirements' else 'none'}" for name in sections
    )
    return _record(
        cli,
        defs,
        "score:specification",
        PHASE,
        {"weight": "light", "phase": PHASE, "effort": EFFORT, "requirements": list(requirements)},
        body,
    )


def _add_run(cli, defs, acceptance: dict, requirement: str, result: str, name: str) -> None:
    _record(
        cli,
        defs,
        "tuner:check-run",
        name,
        {
            "criterion_id": acceptance["id"],
            "revision": "dirty",
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "signed_by": "ayin",
            "requirement": requirement,
            "evidence_kind": "unit",
        },
    )


def _acceptance_with_run(cli, defs, requirement: str, result: str) -> dict:
    acceptance = _record(
        cli,
        defs,
        "score:acceptance",
        f"acc-{requirement}",
        {
            "criterion": requirement,
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": requirement,
        },
    )
    _add_run(cli, defs, acceptance, requirement, result, f"run-{requirement}")
    return acceptance


def _snapshot_effort(store: Path) -> snapshot_mod.EffortView:
    snapshot = snapshot_mod.load_snapshot(open_store(store))
    return next(view for view in snapshot.efforts if view.effort == EFFORT)


def test_task_shows_assignee_and_write_root_from_work_item(store, cli, defs):
    _seed_phase(cli, defs)
    item = _work_item(cli, defs, "w-run", "in_progress", assignee="agent-a", write_root="/w/a")
    row = next(t for t in _snapshot_effort(store).tasks if t.subject == "w-run")
    assert (row.assignee, row.write_root) == ("agent-a", "/w/a")
    assert row.status == "running"
    assert row.running_since is not None
    detail = task_mod.load_task_detail(open_store(store), item["id"])
    assert (detail.assignee, detail.write_root) == ("agent-a", "/w/a")
    assert detail.running_since is not None


def test_journal_shows_assignee_from_work_item(store, cli, defs):
    _seed_phase(cli, defs)
    _work_item(cli, defs, "w-run", "in_progress", assignee="agent-a", write_root="/w/a")
    _record(
        cli,
        defs,
        "conductor:failed-attempt",
        "w-run-attempt",
        {
            "attempted_action": "try it",
            "retry_when": "later",
            "effort": EFFORT,
        },
    )
    items = journal_mod.load_journal(open_store(store), EFFORT)
    item = next(i for i in items if i.subject == "w-run-attempt")
    assert (item.assignee, item.write_root) == ("agent-a", "/w/a")


def test_phase_shows_derived_verified_status(store, cli, defs):
    _seed_phase(cli, defs)
    _spec(cli, defs, "R1", "R2")
    _acceptance_with_run(cli, defs, "R1", "pass")
    detail = phase_mod.load_phase_detail(open_store(store), EFFORT, PHASE)
    assert detail.evidence is not None
    statuses = {row.id: row.status for row in detail.evidence.requirements}
    assert statuses == {"R1": "verified", "R2": "unassessed"}
    requirement = phase_mod.load_requirement_detail(open_store(store), EFFORT, PHASE, "R1")
    assert requirement.status == "verified"


def test_written_failed_assessment_wins_over_passing_check(store, cli, defs):
    _seed_phase(cli, defs)
    _spec(cli, defs, "R1")
    _acceptance_with_run(cli, defs, "R1", "pass")
    _record(
        cli,
        defs,
        "conductor:assessment",
        f"{PHASE}-R1",
        {
            "requirement": "R1",
            "phase": PHASE,
            "effort": EFFORT,
            "missing": "",
            "confidence": "high",
            "status": "failed",
            "next": "execute",
            "level": "implementation",
        },
    )
    detail = phase_mod.load_phase_detail(open_store(store), EFFORT, PHASE)
    assert detail.evidence is not None
    assert [(r.status, r.next) for r in detail.evidence.requirements] == [("failed", "execute")]
    assert detail.evidence.release_ready is False


def _assess(cli, defs, status: str) -> None:
    _record(
        cli,
        defs,
        "conductor:assessment",
        f"{PHASE}-R1",
        {
            "requirement": "R1",
            "phase": PHASE,
            "effort": EFFORT,
            "missing": "",
            "confidence": "high",
            "status": status,
            "next": "execute",
            "level": "implementation",
        },
    )


def test_stale_non_verified_assessment_yields_to_newer_passes(store, cli, defs):
    _seed_phase(cli, defs)
    _spec(cli, defs, "R1")
    acceptance = _acceptance_with_run(cli, defs, "R1", "pass")
    time.sleep(1.1)
    _assess(cli, defs, "blocked")
    detail = phase_mod.load_phase_detail(open_store(store), EFFORT, PHASE)
    assert detail.evidence is not None
    assert [r.status for r in detail.evidence.requirements] == ["blocked"]
    time.sleep(1.1)
    _add_run(cli, defs, acceptance, "R1", "pass", "run-R1-again")
    detail = phase_mod.load_phase_detail(open_store(store), EFFORT, PHASE)
    assert detail.evidence is not None
    assert [r.status for r in detail.evidence.requirements] == ["verified"]
    requirement = phase_mod.load_requirement_detail(open_store(store), EFFORT, PHASE, "R1")
    assert requirement.status == "verified"


def test_snapshot_release_ready_derived(store, cli, defs):
    _seed_phase(cli, defs)
    _spec(cli, defs, "R1", "R2")
    _acceptance_with_run(cli, defs, "R1", "pass")
    view = _snapshot_effort(store)
    assert view.release_ready is False
    _acceptance_with_run(cli, defs, "R2", "pass")
    view = _snapshot_effort(store)
    assert view.release_ready is True
    evidence = view.phases[0].evidence
    assert evidence is not None
    assert (evidence.stage, evidence.release_ready, evidence.release_state) == ("release", True, "")


def test_phase_progress_derived(store, cli, defs):
    _seed_phase(cli, defs)
    _work_item(cli, defs, "w-done", "in_progress", "done")
    _work_item(cli, defs, "w-run", "in_progress")
    _work_item(cli, defs, "w-next")
    view = _snapshot_effort(store)
    row = view.phases[0]
    assert (row.done, row.total, row.in_progress) == (1, 3, ("w-run",))


def test_dashboard_still_reads_written_assignment(store, cli, defs):
    _seed_phase(cli, defs)
    item = _work_item(cli, defs, "w-legacy", "in_progress")
    _record(
        cli,
        defs,
        "conductor:assignment",
        "w-legacy-assign",
        {"work_item": item["subject"], "executor": "legacy-agent", "effort": EFFORT},
    )
    row = next(t for t in _snapshot_effort(store).tasks if t.subject == "w-legacy")
    assert row.assignee == "legacy-agent"
    detail = task_mod.load_task_detail(open_store(store), item["id"])
    assert detail.assignee == "legacy-agent"
    assert len(detail.agent_work) == 1
