"""The phase lookups agree across `orchestra gate`, `wave`, `handoff` and `metrics phases`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import create, make_project, seed_effort
from conftest import REPO_ROOT
from phase_record_support import supersede_all, supersede_phase

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

PHASE = "p1"
REVISED_TITLE = "Revised phase title"


def _orchestra(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ORCHESTRA_STORE", "CANON_STORE"}}
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=root,
        env={**env, "PYTHONPATH": str(REPO_ROOT)},
    )


def _phase_record(project: Project) -> Record:
    return next(r for r in project.records() if r["record_type"] == "score:phase")


def _seed(tmp_path: Path, *, state: str) -> Project:
    project = make_project(tmp_path)
    seed_effort(project)
    phase = _phase_record(project)
    item = create(
        project,
        "score:work-item",
        "p1-t1",
        {"title": "t", "phase": PHASE, "kind": "deliver", "assignee": "", "effort": "alpha"},
        "## Description\n\nDo.\n\n## Approach\n\nDo.",
    )
    for transition in ("in_progress", "done"):
        project.update(item["id"], record_type="score:work-item", transition=transition)
    project.update(phase["id"], record_type="score:phase", transition="in_progress")
    if state == "done":
        project.update(phase["id"], record_type="score:phase", transition="done")
    return project


def _successor_in_state(project: Project, state: str) -> str:
    phase = _phase_record(project)
    successor, _ = supersede_phase(project, phase, payload={"title": REVISED_TITLE})
    project.update(successor["id"], record_type="score:phase", transition="in_progress")
    if state == "done":
        project.update(successor["id"], record_type="score:phase", transition="done")
    return successor["id"]


def _gate(root: Path) -> subprocess.CompletedProcess[str]:
    return _orchestra(root, "gate", PHASE, "--store", str(root))


def _wave(root: Path) -> subprocess.CompletedProcess[str]:
    return _orchestra(root, "wave", "start", PHASE, "--store", str(root))


def _metrics_rows(root: Path) -> list[JsonObject]:
    result = _orchestra(root, "metrics", "phases", "--json", str(root))
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_record_lookups_gate_and_wave_find_the_phase_after_a_supersede(tmp_path: Path) -> None:
    project = _seed(tmp_path, state="done")
    _successor_in_state(project, "done")
    gate = _gate(tmp_path)
    wave = _wave(tmp_path)
    assert gate.returncode == 1
    assert "not found" not in gate.stdout + gate.stderr
    assert "missing verification-task-done" in gate.stdout
    assert wave.returncode == 2
    assert "not found" not in wave.stderr
    assert "no ready work-item" in wave.stderr


def test_record_lookups_metrics_row_comes_from_the_successor_after_a_supersede(
    tmp_path: Path,
) -> None:
    project = _seed(tmp_path, state="done")
    _successor_in_state(project, "done")
    rows = _metrics_rows(tmp_path)
    assert [row["phase"] for row in rows] == [PHASE]


def test_record_lookups_handoff_lists_the_successor_not_the_superseded_record(
    tmp_path: Path,
) -> None:
    project = _seed(tmp_path, state="in_progress")
    predecessor = _phase_record(project)["id"]
    successor = _successor_in_state(project, "in_progress")
    result = _orchestra(tmp_path, "handoff")
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"id: {successor}" in result.stdout
    assert predecessor not in result.stdout


def test_record_lookups_all_four_report_a_phase_with_only_superseded_records_as_absent(
    tmp_path: Path,
) -> None:
    project = _seed(tmp_path, state="in_progress")
    superseded = supersede_all(project, _phase_record(project), payload={"title": REVISED_TITLE})
    gate = _gate(tmp_path)
    wave = _wave(tmp_path)
    handoff = _orchestra(tmp_path, "handoff")
    assert gate.returncode == 2
    assert f"phase {PHASE!r} not found" in gate.stderr
    assert wave.returncode == 2
    assert f"phase {PHASE!r} not found" in wave.stderr
    assert handoff.returncode == 0, handoff.stdout + handoff.stderr
    assert all(record["id"] not in handoff.stdout for record in superseded)
    assert f"**{PHASE}**" not in handoff.stdout


def test_record_lookups_metrics_omits_a_done_phase_with_only_superseded_records(
    tmp_path: Path,
) -> None:
    project = _seed(tmp_path, state="done")
    supersede_all(project, _phase_record(project), payload={"title": REVISED_TITLE})
    assert _metrics_rows(tmp_path) == []
