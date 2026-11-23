from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra import cli
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor import phase_progress
from orchestra.conductor.landing.landing import LandingProofState
from orchestra.conductor.phase_progress import (
    AcceptanceHold,
    ExecutionVerdict,
    PhaseFacts,
    PhaseProgress,
    PhaseProgressError,
    Readiness,
    TaskFact,
    VerifyFacts,
    assess,
)
from orchestra.score.planning.phase import Phase, read_phase
from orchestra.stage.handoff import hook_handoff_sections
from orchestra.tools import BranchState, Git, Unmerged
from orchestra.views import render as views

READY = Readiness(True)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def _start_phase(project: Project, slug: str = "p1") -> Record:
    phase = project.resolve("score:phase", slug)
    project.update(phase["id"], transition="in_progress")
    task = create(
        project,
        "score:work-item",
        f"build-{slug}",
        {"title": "Build", "phase": slug, "kind": "deliver", "assignee": "", "effort": "alpha"},
    )
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")
    return project.resolve("score:phase", slug)


def _verified_facts(
    phase: Record, landing: LandingProofState, branch: BranchState | None
) -> PhaseFacts:
    return PhaseFacts(
        phase=read_phase(phase),
        lifecycle="in_progress",
        spec=READY,
        design=READY,
        tasks_review=READY,
        plan=READY,
        tasks=(TaskFact("t1", "done", ExecutionVerdict("pass", "pass")),),
        acceptances=(AcceptanceHold("a1", True, True),),
        integration="not-required",
        verify=VerifyFacts("", True, (), True),
        landing=landing,
        branch=branch,
        gates=(),
        prerequisites=(),
    )


def _handoff(project: Project, progress: dict[str, PhaseProgress]) -> str:
    return views.render_view(views.HANDOFF, views.load_records(project), progress=progress)


def test_handoff_phase_line_names_stale_proof_as_the_land_reason(project: Project) -> None:
    phase = _start_phase(project)
    progress = assess(_verified_facts(phase, "not-at-head", None))

    text = _handoff(project, {"p1": progress})

    assert "stage: land (stale-proof)" in text


def test_handoff_phase_line_names_awaiting_merge_as_the_close_reason(project: Project) -> None:
    phase = _start_phase(project)
    progress = assess(_verified_facts(phase, "landed", Unmerged("abc", 2)))

    text = _handoff(project, {"p1": progress})

    assert "stage: close (awaiting-merge)" in text
    assert "Awaiting merge" not in text


def test_hook_sections_carry_the_stage_and_reason(project: Project) -> None:
    phase = _start_phase(project)
    progress = assess(_verified_facts(phase, "landed", Unmerged("abc", 2)))

    sections = dict(hook_handoff_sections(views.load_records(project), (), {"p1": progress}))

    assert "stage: close (awaiting-merge)" in sections["alpha"]


def test_status_view_shows_stage_section_instead_of_release(project: Project) -> None:
    phase = _start_phase(project)
    progress = assess(_verified_facts(phase, "not-at-head", None))

    text = views.render_view(views.STATUS, views.load_records(project), progress={"p1": progress})

    assert "### Stage\n- land (stale-proof)" in text
    assert "### Release" not in text


def test_handoff_without_progress_omits_the_stage_line(project: Project) -> None:
    _start_phase(project)

    text = views.render_view(views.HANDOFF, views.load_records(project))

    assert "stage:" not in text


def test_cli_handoff_shows_the_stage_of_an_in_progress_phase(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _start_phase(project)
    monkeypatch.chdir(project.project_root)
    monkeypatch.delenv("CANON_STORE", raising=False)

    assert cli.main(["handoff"]) == 0

    assert "stage: spec" in capsys.readouterr().out


def test_cli_handoff_attention_lists_blocking_questions_before_other_items(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    create(
        project,
        "tuner:finding",
        "needs-answer",
        {
            "claim": "A human decision is required.",
            "basis": "Evidence",
            "invalidated_when": "A human resolves it.",
            "effort": "alpha",
            "needs": "human",
        },
    )
    create(
        project,
        "score:continuity-question",
        "alpha",
        {"owner": "human", "blocking": True, "scope": "alpha"},
    )
    monkeypatch.chdir(project.project_root)
    monkeypatch.delenv("CANON_STORE", raising=False)

    assert cli.main(["handoff"]) == 0
    text = capsys.readouterr().out

    assert text.index("### Blocking Question") < text.index("### Needs Human")


def test_cli_handoff_marks_one_unavailable_phase_and_renders_the_others(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _start_phase(project)
    create(
        project,
        "score:phase",
        "p2",
        {"title": "Phase two", "ordinal": 2, "effort": "alpha"},
    )
    _start_phase(project, "p2")
    real = phase_progress.phase_facts

    def facts(
        target: Project, records: Sequence[Record], phase: Phase, *, git: Callable[[Path], Git]
    ) -> PhaseFacts:
        if phase.subject == "p2":
            raise PhaseProgressError("required phase 'ghost' could not be read")
        return real(target, records, phase, git=git)

    monkeypatch.setattr(phase_progress, "phase_facts", facts)
    monkeypatch.chdir(project.project_root)
    monkeypatch.delenv("CANON_STORE", raising=False)

    assert cli.main(["handoff"]) == 0
    out = capsys.readouterr().out

    assert "**p1**: stage: spec" in out
    assert "**p2**: stage: unavailable: required phase 'ghost' could not be read" in out
