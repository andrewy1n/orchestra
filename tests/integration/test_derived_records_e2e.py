"""A deliver phase driven through `canon` and `orchestra` writes only the records it needs."""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

from dashboard.backend import snapshot as snapshot_mod
from dashboard.backend.phase import load_phase_detail
from dashboard.backend.snapshot import EffortView
from dashboard.backend.store import list_records
from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.derive import phase_progress, release_ready, requirement_status

PHASE = "dr-phase"
EFFORT = "dr-effort"
IMPL = f"{PHASE}-impl"
REST = f"{PHASE}-rest"
ASSIGNEE = "inline"
REQUIREMENT_TEXT = "R1: the temp phase is verified from its check-run"
DESCRIPTION_MARKER = "derived-records-description-marker"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
SPEC_BODY = (
    f"## Requirements\n\n{REQUIREMENT_TEXT}\n\n"
    "## Acceptance criteria\n\nnone\n\n## Constraints\n\nnone\n\n"
    "## Non-goals\n\nnone\n\n## Invariants\n\nnone\n\n## Assumptions\n\nnone\n"
)
TRACKED_ABSENT = (
    "conductor:assignment",
    "conductor:release",
    "conductor:assessment",
    "score:position",
)


@dataclass(frozen=True)
class Run:
    store: Path
    code: Path
    head: str
    impl_id: str
    acceptance_id: str
    work_root: str
    before_check: Counter[str]
    after_first_check: Counter[str]
    after_second_check: Counter[str]
    after_close: Counter[str]
    first_check: subprocess.CompletedProcess[str]
    second_check: subprocess.CompletedProcess[str]
    brief: str
    effort_view: EffortView
    records: list[Record]


class World:
    def __init__(self, root: Path) -> None:
        self.store = make_git_repo()
        self.code = make_git_repo()
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()

    def run(
        self, tool: str, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=str(cwd or self.store),
            env=self.env,
        )

    def canon(self, *args: str) -> Record:
        result = self.run("canon", *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)["record"]

    def create(
        self, record_type: str, subject: str, payload: dict[str, object], body: str | None = None
    ) -> Record:
        args = [
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
        ]
        if body is not None:
            args += ["--body", body]
        return self.canon(*args)

    def update(
        self,
        record: Record,
        transition: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> Record:
        args = [
            "update",
            "--type",
            record["record_type"],
            "--id",
            record["id"],
            "--expected-revision",
            record["revision"],
        ]
        if transition is not None:
            args += ["--transition", transition]
        if payload is not None:
            args += ["--payload", json.dumps(payload)]
        return self.canon(*args)

    def counts(self) -> Counter[str]:
        result = self.run("canon", "list", "--format", "json")
        assert result.returncode == 0, result.stdout + result.stderr
        return Counter(r["record_type"] for r in json.loads(result.stdout)["records"])

    def check(self, acceptance_id: str) -> subprocess.CompletedProcess[str]:
        return self.run(
            "orchestra",
            "check",
            "--acceptance",
            acceptance_id,
            "--cwd",
            str(self.code),
            "--store",
            str(self.store),
        )


def _work_item(world: World, slug: str, description: str) -> Record:
    return world.create(
        "score:work-item",
        slug,
        {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "unassigned",
            "effort": EFFORT,
            "requirements": ["R1"],
        },
        f"## Description\n\n{description}",
    )


def _print_write_table(title: str, before: Counter[str], after: Counter[str]) -> None:
    rows = sorted(set(before) | set(after))
    print(f"\n{title}\nrecord type                      written")
    for record_type in rows:
        print(f"{record_type:<32} {after[record_type] - before[record_type]:>7}")
    print(f"{'total':<32} {sum(after.values()) - sum(before.values()):>7}")


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Run]:
    root = tmp_path_factory.mktemp("derived-records")
    world = World(root)
    patch = pytest.MonkeyPatch()
    patch.setenv("HOME", world.env["HOME"])
    result = world.run("canon", "init", "--schemas", "score,conductor,tuner,composer")
    assert result.returncode == 0, result.stdout + result.stderr

    head = git(world.code, "rev-parse", "HEAD").stdout.strip()
    work_root = str(world.code)

    world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    world.create("score:phase", PHASE, {"title": PHASE, "ordinal": 1, "effort": EFFORT}, PHASE_BODY)
    world.create(
        "score:specification",
        PHASE,
        {"weight": "light", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        SPEC_BODY,
    )
    impl = _work_item(world, IMPL, DESCRIPTION_MARKER)
    _work_item(world, REST, "not started")
    acceptance = world.create(
        "score:acceptance",
        IMPL,
        {
            "criterion": "c",
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    before_dispatch = world.counts()

    impl = world.update(impl, "in_progress", {"assignee": ASSIGNEE, "write_root": work_root})
    brief = world.run("orchestra", "brief", IMPL)
    assert brief.returncode == 0, brief.stdout + brief.stderr

    before_check = world.counts()
    first_check = world.check(acceptance["id"])
    after_first_check = world.counts()
    second_check = world.check(acceptance["id"])
    after_second_check = world.counts()

    world.create(
        "conductor:execution-report",
        IMPL,
        {"work_item": IMPL, "result": "pass", "verdict": "pass", "revision": head},
        "subject: dr\nresult: pass\n",
    )
    batch = world.store / "close.ndjson"
    batch.write_text(
        json.dumps(
            {
                "op": "update",
                "type": "score:work-item",
                "id": impl["id"],
                "transition": "done",
                "expected_revision": "@current",
            }
        )
        + "\n"
    )
    applied = world.run("canon", "apply", str(batch))
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["ok"] is True
    after_close = world.counts()
    validate = world.run("canon", "validate")
    assert validate.returncode == 0, validate.stdout + validate.stderr

    _print_write_table("whole scenario", Counter(), after_close)
    _print_write_table("dispatch to close", before_dispatch, after_close)

    target = open_store(world.store)
    records = [r for t in after_close for r in list_records(target, t)]
    snapshot = snapshot_mod.load_snapshot(target)
    effort_view = next(view for view in snapshot.efforts if view.effort == EFFORT)
    yield Run(
        store=world.store,
        code=world.code,
        head=head,
        impl_id=impl["id"],
        acceptance_id=acceptance["id"],
        work_root=work_root,
        before_check=before_check,
        after_first_check=after_first_check,
        after_second_check=after_second_check,
        after_close=after_close,
        first_check=first_check,
        second_check=second_check,
        brief=brief.stdout,
        effort_view=effort_view,
        records=records,
    )
    patch.undo()


def test_no_assignment_release_or_position_records_are_written(run: Run) -> None:
    for record_type in TRACKED_ABSENT:
        assert run.after_close[record_type] == 0, record_type


def test_no_assignment_in_progress_update_carries_assignee_and_write_root(run: Run) -> None:
    row = next(t for t in run.effort_view.tasks if t.subject == IMPL)
    assert (row.assignee, row.write_root) == (ASSIGNEE, run.work_root)


def test_no_assignment_brief_quotes_claims_and_shows_assignee_and_write_root(run: Run) -> None:
    assert DESCRIPTION_MARKER in run.brief
    assert REQUIREMENT_TEXT in run.brief
    assert ASSIGNEE in run.brief
    assert run.work_root in run.brief


def test_reuse_second_check_returns_existing_check_run_and_writes_nothing(run: Run) -> None:
    assert run.first_check.returncode == 0, run.first_check.stdout + run.first_check.stderr
    assert run.second_check.returncode == 0, run.second_check.stdout + run.second_check.stderr
    first = json.loads(run.first_check.stdout)
    second = json.loads(run.second_check.stdout)
    assert first["reused"] is False
    assert second["reused"] is True
    assert second["record"]["id"] == first["record"]["id"]
    assert run.after_first_check["tuner:check-run"] - run.before_check["tuner:check-run"] == 1
    assert run.after_second_check == run.after_first_check


def test_reuse_leaves_one_check_run_per_acceptance_and_revision(run: Run) -> None:
    runs = [
        r
        for r in run.records
        if r["record_type"] == "tuner:check-run"
        and r["payload"]["criterion_id"] == run.acceptance_id
    ]
    assert [r["payload"]["revision"] for r in runs] == [run.head]
    assert runs[0]["id"] == json.loads(run.second_check.stdout)["record"]["id"]


def test_verified_requirement_derives_from_passing_check_run_at_head(run: Run) -> None:
    statuses = requirement_status(run.records, PHASE, run.head)
    assert statuses["R1"].status == "verified"
    assert release_ready(run.records, PHASE, run.head)
    assert run.after_close["conductor:assessment"] == 0
    assert run.after_close["conductor:release"] == 0


def test_verified_requirement_is_not_verified_at_another_revision(run: Run) -> None:
    assert requirement_status(run.records, PHASE, "0" * 40)["R1"].status == "unverified"


def test_verified_dashboard_phase_shows_requirement_verified_and_release_ready(run: Run) -> None:
    detail = load_phase_detail(open_store(run.store), EFFORT, PHASE)
    assert detail.evidence is not None
    assert {row.id: row.status for row in detail.evidence.requirements} == {"R1": "verified"}
    assert detail.evidence.release_ready


def test_progress_dashboard_phase_counts_work_item_states(run: Run) -> None:
    phase = next(p for p in run.effort_view.phases if p.subject == PHASE)
    assert (phase.done, phase.total) == (1, 2)
    assert phase.in_progress == ()
    progress = phase_progress(run.records, PHASE)
    assert (progress.done, progress.total) == (1, 2)
    assert progress.counts == {"planned": 1, "in_progress": 0, "done": 1}
