from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort
from conftest import REPO_ROOT, git, make_git_repo

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.metrics.phases import build_phase_rows

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.gates import landing_branch
from dashboard.backend.landing import phase_landing
from dashboard.backend.phase import load_phase_detail

EFFORT = "alpha"
PHASE = "p1"
HEAD = "abc1234def5678"
ROOT = Path("/repo")


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, EFFORT, PHASE)
    create(project, "score:effort", "beta", {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", "p2", {"title": "Phase two", "ordinal": 2, "effort": EFFORT})
    project.project_root.joinpath("orchestra.toml").write_text(
        (REPO_ROOT / "orchestra.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return project


def _packet_payload(effort: str = EFFORT, phase: str = PHASE) -> JsonObject:
    return {"phase": phase, "effort": effort, "revision": HEAD, "base": "main", "kind": "demo"}


def _packet(project: Project, effort: str = EFFORT) -> str:
    return create(project, "conductor:proof-packet", PHASE, _packet_payload(effort))["id"]


def _close_phase(project: Project, *, landing: bool = False) -> str:
    phase = project.resolve("score:phase", PHASE)
    body = phase.get("body") or ""
    if landing:
        body += "\n## Landing\n"
    project.update(phase["id"], transition="in_progress", body=body)
    task = create(
        project,
        "score:work-item",
        "build-it",
        {
            "title": "t",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
        },
    )
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")
    return phase["id"]


def _move_to_beta(project: Project) -> None:
    for record_type, subject in (("score:phase", PHASE), ("score:work-item", "build-it")):
        record = project.resolve(record_type, subject)
        project.update(record["id"], payload={"effort": "beta"})


def _correct_into_other_phase(project: Project, packet_id: str) -> None:
    project.correct(packet_id, payload=_packet_payload(phase="p2"))


def _metrics_find_packet(project: Project, effort: str) -> bool:
    phase = project.resolve("score:phase", PHASE)
    project.update(phase["id"], transition="done")
    row = next(r for r in build_phase_rows(project.project_root) if r.phase == PHASE)
    return row.landing_source == "conductor:proof-packet"


def _dashboard_finds_packet(project: Project, effort: str) -> bool:
    return load_phase_detail(project, effort, PHASE).proof is not None


READERS = [_metrics_find_packet, _dashboard_finds_packet]
Reader = Callable[[Project, str], bool]


@pytest.mark.parametrize("reader", READERS)
def test_r18_readers_use_the_packet_of_the_phase_effort(project: Project, reader: Reader) -> None:
    _close_phase(project, landing=True)
    _packet(project)

    assert reader(project, EFFORT)


@pytest.mark.parametrize("reader", READERS)
def test_r18_readers_ignore_a_corrected_proof_packet(project: Project, reader: Reader) -> None:
    _close_phase(project, landing=True)
    _correct_into_other_phase(project, _packet(project))

    assert not reader(project, EFFORT)


@pytest.mark.parametrize("reader", READERS)
def test_r18_readers_ignore_a_proof_packet_of_another_effort(
    project: Project, reader: Reader
) -> None:
    _close_phase(project, landing=True)
    _packet(project)
    _move_to_beta(project)

    assert not reader(project, "beta")


@pytest.mark.parametrize("reader", READERS)
def test_r18_views_metrics_and_the_dashboard_ignore_a_corrected_proof_packet_and_one_of_another_effort(
    project: Project, reader: Reader
) -> None:
    _close_phase(project, landing=True)
    _packet(project)
    _correct_into_other_phase(project, _packet(project))
    _move_to_beta(project)

    assert not reader(project, "beta")


def _branch_repo() -> Path:
    root = make_git_repo()
    git(root, "branch", "-M", "main")
    git(root, "checkout", "-qb", "feat/x")
    (root / "f.txt").write_text("f")
    git(root, "add", "f.txt")
    git(root, "commit", "-qm", "f")
    git(root, "checkout", "-q", "main")
    return root


def test_r19_dashboard_reads_a_branch_line_without_backticks() -> None:
    root = _branch_repo()

    state = phase_landing(root, "## Landing\n\n- Branch: feat/x\n", PHASE)

    assert state is not None
    assert state.branch == "feat/x"
    assert state.exists
    assert state.ahead == 1


def test_r19_dashboard_branch_is_the_phase_branch_when_the_section_names_none() -> None:
    root = _branch_repo()

    state = phase_landing(root, "## Landing\n", PHASE)

    assert state is not None
    assert state.branch == f"phase/{PHASE}"
    assert not state.exists


def test_r19_dashboard_has_no_branch_without_a_landing_section() -> None:
    assert phase_landing(_branch_repo(), "## Problem\n\nx\n", PHASE) is None
    assert landing_branch("## Problem\n\nx\n", PHASE, ROOT) is None


def test_r19_gate_refs_use_the_landing_place_branch() -> None:
    assert landing_branch("## Landing\n\n* Branch: `feat/y`\n", PHASE, ROOT) == "feat/y"
    assert landing_branch("## Landing\n", PHASE, ROOT) == f"phase/{PHASE}"
