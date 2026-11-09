"""Tests for the phase progress figures (R8, R9, R10, R11, R12, R17)."""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import helpers as h
import pytest
from conftest import REPO_ROOT, SCHEMA_FILES, build_store, run_cli

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend import phase as phase_mod
from dashboard.backend import snapshot as snapshot_mod
from dashboard.backend.landing import Landing
from dashboard.backend.phase import (
    IntegrationView,
    PhaseEvidence,
    PhaseRow,
    RequirementRow,
)
from dashboard.backend.progress import build_progress, derive_stages
from dashboard.backend.snapshot import NeedsYouItem
from dashboard.backend.task import TaskRow
from orchestra.canon.project import open_store

PHASE = "p-one"
EFFORT = "alpha"
APPROVED = frozenset({"spec", "design", "plan"})
MERGED = Landing(branch="phase/p-one", exists=True, ahead=0, merged=True)
UNMERGED = Landing(branch="phase/p-one", exists=True, ahead=2, merged=False)


def _task(
    subject: str,
    status: str = "done",
    wave: int | None = 1,
    attempts: int = 0,
    phase: str = PHASE,
) -> TaskRow:
    return TaskRow(
        id=f"id-{subject}",
        subject=subject,
        title=subject,
        phase=phase,
        assignee="",
        wave=wave,
        status=status,
        attempts=attempts,
    )


def _requirement(requirement: str, status: str = "verified") -> RequirementRow:
    return RequirementRow(PHASE, requirement, f"text of {requirement}", status, "", None, 1)


def _evidence(*statuses: str, weight: str = "full") -> PhaseEvidence:
    return PhaseEvidence(
        phase=PHASE,
        weight=weight,
        requirements=tuple(_requirement(f"R{i}", s) for i, s in enumerate(statuses, start=1)),
        stage="release",
        integration=IntegrationView("", ""),
        release_ready=False,
        decisions=(),
        non_goals="",
    )


def _phase(
    tasks: list[TaskRow],
    *requirement_statuses: str,
    body: str = "",
    state: str = "in_progress",
) -> PhaseRow:
    counted = [t for t in tasks if t.phase == PHASE and t.status != "withdrawn"]
    return PhaseRow(
        subject=PHASE,
        title="One",
        ordinal=1,
        state=state,
        done=sum(1 for t in counted if t.status == "done"),
        total=len(counted),
        evidence=_evidence(*requirement_statuses) if requirement_statuses else None,
        body=body,
    )


def _need(item_id: str, text: str, phase: str = PHASE, status: str = "open") -> NeedsYouItem:
    return NeedsYouItem(
        kind="open-question", id=item_id, subject=item_id, text=text, phase=phase, status=status
    )


def _progress(
    tasks: list[TaskRow],
    *requirement_statuses: str,
    needs: list[NeedsYouItem] | None = None,
    landing: Landing | None = MERGED,
    review: bool = True,
    body: str = "",
    approved=APPROVED,
):
    return build_progress(
        _phase(tasks, *requirement_statuses, body=body),
        tasks,
        needs or [],
        landing=landing,
        approved=approved,
        review_passed_at_head=review,
    )


def test_r8_counts_done_running_and_remaining():
    tasks = [
        _task("a", "done", 1),
        _task("b", "done", 1),
        _task("c", "running", 2),
        _task("d", "ready", 2),
        _task("e", "waiting", 3),
    ]

    figures = _progress(tasks).tasks

    assert (figures.done, figures.running, figures.remaining, figures.total) == (2, 1, 2, 5)


def test_r8_label_gives_done_count_total_and_current_wave():
    tasks = [
        _task("a", "done", 1),
        _task("b", "running", 2),
        _task("c", "waiting", 3),
    ]

    figures = _progress(tasks).tasks

    assert figures.wave == 2
    assert "1 of 3" in figures.label
    assert "wave 2" in figures.label


def test_r8_current_wave_is_the_lowest_wave_with_an_unfinished_task():
    tasks = [
        _task("a", "done", 1),
        _task("b", "withdrawn", 1),
        _task("c", "waiting", 4),
        _task("d", "ready", 3),
        _task("e", "done", 5),
    ]

    assert _progress(tasks).tasks.wave == 3


def test_r8_no_current_wave_when_every_task_is_done():
    tasks = [_task("a", "done", 1), _task("b", "done", 2)]

    figures = _progress(tasks).tasks

    assert figures.wave is None
    assert "2 of 2" in figures.label
    assert "wave" not in figures.label


def test_r8_ignores_tasks_of_other_phases_and_withdrawn_tasks():
    tasks = [
        _task("a", "done", 1),
        _task("b", "waiting", 2),
        _task("gone", "withdrawn", 1),
        _task("other", "running", 1, phase="p-two"),
    ]

    figures = _progress(tasks).tasks

    assert (figures.done, figures.running, figures.remaining, figures.total) == (1, 0, 1, 2)


def test_r8_result_holds_weight_and_stages_from_derive_stages():
    tasks = [_task("a", "done"), _task("b", "running", 2)]

    result = _progress(tasks, "verified", "unverified")

    expected = derive_stages(
        weight="full",
        phase_state="in_progress",
        approved=APPROVED,
        task_states=["done", "running"],
        requirement_statuses=["verified", "unverified"],
        review_passed_at_head=True,
        branch_merged=True,
    )
    assert result.weight == "full"
    assert list(result.stages) == expected


def test_r8_weight_is_light_when_the_phase_evidence_is_light():
    tasks = [_task("a", "done")]
    phase = _phase(tasks)
    light = PhaseRow(**{**phase.__dict__, "evidence": _evidence("verified", weight="light")})

    result = build_progress(
        light, tasks, [], landing=MERGED, approved=APPROVED, review_passed_at_head=True
    )

    assert result.weight == "light"
    assert result.stages[0].id == "tasks"


def test_r9_phase_with_no_tasks_reports_no_tasks_yet():
    figures = _progress([]).tasks

    assert (figures.done, figures.running, figures.remaining, figures.total) == (0, 0, 0, 0)
    assert figures.wave is None
    assert figures.label == "no tasks yet"


def test_r9_only_withdrawn_tasks_still_reports_no_tasks_yet():
    figures = _progress([_task("gone", "withdrawn")]).tasks

    assert figures.total == 0
    assert figures.label == "no tasks yet"


def test_r10_requirements_report_proven_out_of_total():
    result = _progress([_task("a")], "verified", "failed", "verified", "unverified")

    figures = result.requirements

    assert (figures.proven, figures.total) == (2, 4)
    assert "2 of 4" in figures.label


def test_r10_all_requirements_proven():
    figures = _progress([_task("a")], "verified", "verified").requirements

    assert (figures.proven, figures.total) == (2, 2)
    assert "2 of 2" in figures.label


def test_r10_phase_without_requirements_says_no_requirements():
    figures = _progress([_task("a")]).requirements

    assert (figures.proven, figures.total) == (0, 0)
    assert figures.label == "no requirements"


def test_r10_phase_with_empty_evidence_says_no_requirements():
    tasks = [_task("a")]
    phase = PhaseRow(**{**_phase(tasks).__dict__, "evidence": _evidence()})

    result = build_progress(
        phase, tasks, [], landing=MERGED, approved=APPROVED, review_passed_at_head=True
    )

    assert result.requirements.label == "no requirements"


def test_r11_repairs_absent_without_fix_task_or_attempt():
    tasks = [_task("a"), _task("b", "running", 2)]

    assert _progress(tasks).repairs is None


def test_r11_repairs_present_with_a_fix_work_item():
    tasks = [_task("a"), _task("fix-a-flake", "running", 2)]

    repairs = _progress(tasks).repairs

    assert repairs is not None
    assert (repairs.used, repairs.limit) == (1, 3)
    assert "1 of 3" in repairs.label


def test_r11_repairs_present_when_a_task_was_redispatched():
    tasks = [_task("a", "running", attempts=1)]

    repairs = _progress(tasks).repairs

    assert repairs is not None
    assert (repairs.used, repairs.limit) == (0, 3)
    assert "0 of 3" in repairs.label


def test_r11_fix_tasks_of_other_phases_do_not_count():
    tasks = [_task("a"), _task("fix-elsewhere", "running", 1, phase="p-two")]

    assert _progress(tasks).repairs is None


def test_r11_counts_every_fix_task_in_the_phase():
    tasks = [_task("a"), _task("fix-one"), _task("fix-two", "running", 2)]

    repairs = _progress(tasks).repairs

    assert repairs is not None
    assert repairs.used == 2


def test_r11_limit_reads_the_retry_max_fix_tasks_run_fact():
    tasks = [_task("fix-one", "running", 1)]

    repairs = _progress(tasks, body="## Run facts\n\n- retry_max_fix_tasks: 5\n").repairs

    assert repairs is not None
    assert (repairs.used, repairs.limit) == (1, 5)
    assert "1 of 5" in repairs.label


def test_r11_limit_ignores_the_redispatch_run_fact():
    tasks = [_task("fix-one", "running", 1)]

    repairs = _progress(tasks, body="retry_max_redispatches: 7\n").repairs

    assert repairs is not None
    assert repairs.limit == 3


def _clean() -> list[TaskRow]:
    return [_task("a"), _task("b")]


def test_r12_nothing_blocking_says_nothing_blocks_close():
    result = _progress(_clean(), "verified")

    assert result.blockers.shown == ()
    assert result.blockers.more == 0
    assert result.blockers.text == "Nothing blocks close"


def test_r12_one_blocker_is_listed_alone():
    result = _progress(_clean(), "verified", landing=UNMERGED)

    assert len(result.blockers.shown) == 1
    assert result.blockers.more == 0
    assert "more" not in result.blockers.text
    assert result.blockers.shown[0] in result.blockers.text


def test_r12_two_blockers_are_both_listed_without_a_remainder():
    needs = [_need("q1", "Pick a theme"), _need("q2", "Confirm the scope")]

    blockers = _progress(_clean(), "verified", needs=needs).blockers

    assert blockers.shown == ("Pick a theme", "Confirm the scope")
    assert blockers.more == 0
    assert "more" not in blockers.text


def test_r12_three_blockers_list_two_and_count_the_rest():
    needs = [_need("q1", "Pick a theme"), _need("q2", "Confirm the scope"), _need("q3", "Third")]

    blockers = _progress(_clean(), "verified", needs=needs).blockers

    assert blockers.shown == ("Pick a theme", "Confirm the scope")
    assert blockers.more == 1
    assert "+1 more" in blockers.text


def test_r12_five_blockers_count_three_more():
    needs = [_need(f"q{i}", f"Question {i}") for i in range(1, 6)]

    blockers = _progress(_clean(), "verified", needs=needs).blockers

    assert len(blockers.shown) == 2
    assert blockers.more == 3
    assert "+3 more" in blockers.text


def test_r12_open_needs_you_items_of_this_phase_block_close():
    needs = [
        _need("q1", "Mine"),
        _need("q2", "Other phase", phase="p-two"),
        _need("q3", "Settled", status="done"),
    ]

    blockers = _progress(_clean(), "verified", needs=needs).blockers

    assert blockers.shown == ("Mine",)


def test_r12_unfinished_tasks_block_close():
    tasks = [_task("a"), _task("b", "running", 2)]

    blockers = _progress(tasks, "verified").blockers

    assert len(blockers.shown) == 1
    assert "task" in blockers.shown[0].lower()


def test_r12_phase_with_no_tasks_has_no_tasks_blocker():
    blockers = _progress([], "verified").blockers

    assert blockers.shown == ()
    assert blockers.text == "Nothing blocks close"


def test_r12_unproven_requirements_block_close():
    blockers = _progress(_clean(), "verified", "failed").blockers

    assert len(blockers.shown) == 1
    assert "requirement" in blockers.shown[0].lower()


def test_r12_missing_passing_review_blocks_close():
    blockers = _progress(_clean(), "verified", review=False).blockers

    assert len(blockers.shown) == 1
    assert "review" in blockers.shown[0].lower()


def test_r12_unmerged_branch_blocks_close():
    blockers = _progress(_clean(), "verified", landing=UNMERGED).blockers

    assert len(blockers.shown) == 1
    assert "branch" in blockers.shown[0].lower()


def test_r12_a_phase_without_a_landing_has_no_branch_blocker():
    blockers = _progress(_clean(), "verified", landing=None).blockers

    assert blockers.shown == ()


def test_r12_every_kind_of_blocker_together_lists_two_and_counts_the_rest():
    tasks = [_task("a"), _task("b", "waiting", 2)]
    needs = [_need("q1", "Pick a theme")]

    blockers = _progress(tasks, "failed", needs=needs, landing=UNMERGED, review=False).blockers

    assert blockers.shown[0] == "Pick a theme"
    assert len(blockers.shown) == 2
    assert blockers.more == 3
    assert "+3 more" in blockers.text


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    paths: list[str] = []
    for source in SCHEMA_FILES:
        module = json.loads(source.read_text())
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


def _record(cli, defs, record_type: str, subject: str, payload: dict, body: str | None = None):
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


def _work_item(cli, defs, subject: str, *states: str) -> None:
    payload = {
        "title": subject,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
    }
    record = _record(cli, defs, "score:work-item", subject, payload)
    if states:
        h.transition(cli, "score:work-item", record, *states)


def _spec(cli, defs, *requirements: str) -> None:
    lines = "\n".join(f"{r}: text of {r}" for r in requirements)
    sections = defs["score:specification"].get("required_sections") or []
    body = "\n\n".join(
        f"## {name}\n\n{lines if name == 'Requirements' else 'none'}" for name in sections
    )
    _record(
        cli,
        defs,
        "score:specification",
        PHASE,
        {"weight": "light", "phase": PHASE, "effort": EFFORT, "requirements": list(requirements)},
        body,
    )


def _passing_run(cli, defs, requirement: str) -> None:
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
    _record(
        cli,
        defs,
        "tuner:check-run",
        f"run-{requirement}",
        {
            "criterion_id": acceptance["id"],
            "revision": "dirty",
            "result": "pass",
            "effort": EFFORT,
            "method": "check",
            "signed_by": "ayin",
            "requirement": requirement,
            "evidence_kind": "unit",
        },
    )


def test_r17_task_counts_equal_the_phase_page(store, cli, defs):
    _seed_phase(cli, defs)
    _work_item(cli, defs, "w-done", "in_progress", "done")
    _work_item(cli, defs, "w-run", "in_progress")
    _work_item(cli, defs, "w-next")
    target = open_store(store)
    view = next(v for v in snapshot_mod.load_snapshot(target).efforts if v.effort == EFFORT)
    row = view.phases[0]
    page = phase_mod.load_phase_detail(target, EFFORT, PHASE)

    figures = build_progress(
        row,
        view.tasks,
        view.needs_you,
        landing=None,
        approved=APPROVED,
        review_passed_at_head=False,
    ).tasks

    page_tasks = [t for t in page.tasks if t.status != "withdrawn"]
    assert figures.done == sum(1 for t in page_tasks if t.status == "done")
    assert figures.running == sum(1 for t in page_tasks if t.status == "running")
    assert figures.total == len(page_tasks)
    assert (figures.done, figures.running, figures.remaining, figures.total) == (1, 1, 1, 3)


def test_r17_requirement_counts_equal_the_phase_evidence_rows(store, cli, defs):
    _seed_phase(cli, defs)
    _work_item(cli, defs, "w-done", "in_progress", "done")
    _spec(cli, defs, "R1", "R2", "R3")
    _passing_run(cli, defs, "R1")
    target = open_store(store)
    view = next(v for v in snapshot_mod.load_snapshot(target).efforts if v.effort == EFFORT)
    page = phase_mod.load_phase_detail(target, EFFORT, PHASE)

    figures = build_progress(
        view.phases[0],
        view.tasks,
        view.needs_you,
        landing=None,
        approved=APPROVED,
        review_passed_at_head=False,
    ).requirements

    assert page.evidence is not None
    rows = page.evidence.requirements
    assert figures.total == len(rows) == 3
    assert figures.proven == sum(1 for r in rows if r.status == "verified")
    assert figures.proven == 1
