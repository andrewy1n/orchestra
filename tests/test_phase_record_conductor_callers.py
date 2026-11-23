from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from canon_support import create, make_project
from conductor_support import FakeStates

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue, Record
from orchestra.conductor.landing import gate
from orchestra.conductor.landing.landing import LandingPlace, phase_place
from orchestra.conductor.phases.progress import close
from orchestra.conductor.phases.workflow.workflow import WorkflowRunError, step_stage
from orchestra.conductor.tasks import wave
from orchestra.score.planning.phase import Phase

PHASE = "ph"
EFFORT = "ef"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
PLAIN_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
Spy = list[tuple[Phase, LandingPlace]]


def _phase(project: Project, body: str) -> Record:
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    return create(
        project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT}, body
    )


def _landing(project: Project, head_sha: str = HEAD) -> Record:
    return create(
        project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": head_sha,
            "result": "success",
        },
    )


def _store_without_validation(
    project: Project, record: Record, field: str, value: JsonValue
) -> None:
    store, _ = project._session()
    changed = Record(**record)
    changed["payload"] = {**record["payload"], field: value}
    store.write_record(changed, expected_revision=record["revision"])


def _spy(monkeypatch: pytest.MonkeyPatch, module: ModuleType) -> Spy:
    calls: Spy = []

    def resolve(phase: Phase, store: Path) -> LandingPlace:
        place = phase_place(phase, store)
        calls.append((phase, place))
        return place

    monkeypatch.setattr(module, "phase_place", resolve, raising=False)
    return calls


def _through_gate(project: Project) -> None:
    gate.gate_terms(project, PHASE)


def _through_close(project: Project) -> None:
    _landing(project)
    close.close_phase(project, project.project_root, PHASE, FakeStates("MERGED", HEAD))


def _through_wave(project: Project) -> None:
    wave.end(project, project.project_root, PHASE)


CALLERS: dict[str, tuple[ModuleType, Callable[[Project], None]]] = {
    "gate": (gate, _through_gate),
    "close": (close, _through_close),
    "wave": (wave, _through_wave),
}


def _resolved_places(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> dict[str, tuple[Spy, str]]:
    current = project.resolve("score:phase", PHASE)["id"]
    resolved: dict[str, tuple[Spy, str]] = {}
    for name, (module, run) in CALLERS.items():
        calls = _spy(monkeypatch, module)
        run(project)
        resolved[name] = (calls, current)
    return resolved


def test_r3_gate_close_and_wave_resolve_the_landing_place_of_the_same_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = make_project(tmp_path / "store")
    repo = make_project(tmp_path / "landing-repo").project_root
    tree = tmp_path / "elsewhere" / "tree"
    _phase(
        project,
        PLAIN_BODY
        + f"\n## Landing\n\nRepo: {repo}\nWorktree: {tree}\nBranch: feature/ph\nBase: develop\n",
    )
    expected = LandingPlace(repo=repo, worktree=tree, branch="feature/ph", base="develop")

    resolved = _resolved_places(project, monkeypatch)

    for name, (calls, current) in resolved.items():
        assert [(phase.id, place) for phase, place in calls] == [(current, expected)], name


def test_r4_gate_close_and_wave_resolve_the_default_layout_without_a_landing_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = make_project(tmp_path / "store")
    root = project.project_root
    _phase(project, PLAIN_BODY)
    expected = LandingPlace(
        repo=root, worktree=root / ".worktrees" / PHASE, branch=f"phase/{PHASE}", base="main"
    )

    resolved = _resolved_places(project, monkeypatch)

    for name, (calls, current) in resolved.items():
        assert [(phase.id, place) for phase, place in calls] == [(current, expected)], name


def test_r10_close_names_the_landing_record_and_field_when_head_sha_is_not_a_string(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    _phase(project, PLAIN_BODY)
    landing = _landing(project)
    _store_without_validation(project, landing, "head_sha", 123)

    with pytest.raises(RecordShapeError, match=rf"{landing['id']}.*head_sha"):
        close.close_phase(project, project.project_root, PHASE, FakeStates("OPEN", HEAD))


def test_r10_workflow_names_the_landing_record_and_field_when_head_sha_is_not_a_string(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    _phase(project, PLAIN_BODY + "\n## Landing\n\nBranch: phase/ph\n")
    landing = _landing(project)
    create(
        project,
        "conductor:proof-packet",
        PHASE,
        {"phase": PHASE, "effort": EFFORT, "revision": HEAD, "base": "main", "kind": "claims"},
    )
    _store_without_validation(project, landing, "head_sha", 123)

    with pytest.raises(WorkflowRunError, match=rf"{landing['id']}.*head_sha"):
        step_stage(project, project.records(), PHASE, "land")


def test_r10_workflow_names_the_phase_record_and_field_when_ordinal_is_not_an_integer(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    phase = _phase(project, PLAIN_BODY + "\n## Landing\n\nBranch: phase/ph\n")
    _store_without_validation(project, phase, "ordinal", "first")

    with pytest.raises(WorkflowRunError, match=rf"{phase['id']}.*ordinal"):
        step_stage(project, project.records(), PHASE, "land")


def test_r10_gate_names_the_phase_record_and_field_when_effort_is_not_a_string(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    phase = _phase(project, PLAIN_BODY)
    _store_without_validation(project, phase, "effort", 7)

    with pytest.raises(RecordShapeError, match=rf"{phase['id']}.*effort"):
        gate.gate_terms(project, PHASE)
