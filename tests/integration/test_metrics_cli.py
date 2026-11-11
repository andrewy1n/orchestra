"""`orchestra metrics` reads a seeded temporary store through the real entry point."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import create, make_project
from conftest import REPO_ROOT
from test_metrics_phases import Clock, _check_run, _landing, _phase, _specification

from orchestra.canon.project import Project

ROW_FIELDS = {
    "effort",
    "weight",
    "tasks",
    "landing_time",
    "elapsed_seconds",
    "review_rounds",
    "failed_check_runs",
    "human_decisions",
    "operations_per_task",
    "repairs_by_cause",
}
RANKING_WORDS = re.compile(
    r"\b(better|worse|best|worst|faster|slower|improv\w*|regress\w*|winner|loser|ranks?)\b",
    re.IGNORECASE,
)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    return Clock(monkeypatch)


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in {"ORCHESTRA_STORE", "CANON_STORE"}}


def _metrics(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    split = next((i for i, a in enumerate(args) if a.startswith("--")), len(args))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "metrics", *args[:split], str(root), *args[split:]],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=_env(),
    )


def _landed(project: Project, clock: Clock, phase: str, day: int, weight: str, tasks: int) -> None:
    clock.at(f"2026-11-{day:02d}T00:00:00+00:00")
    _phase(project, phase, "ef", weight=weight, tasks=tasks)
    clock.at(f"2026-11-{day:02d}T06:00:00+00:00")
    _check_run(project, phase, "ef")
    clock.at(f"2026-11-{day:02d}T12:00:00+00:00")
    _landing(project, phase)


def _seed_three_done_one_planned(root: Path, clock: Clock) -> Project:
    project = make_project(root)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    _landed(project, clock, "ph-a", 2, "light", 1)
    _landed(project, clock, "ph-b", 3, "full", 2)
    _landed(project, clock, "ph-c", 4, "light", 3)
    _phase(project, "ph-planned", "ef", tasks=1, done=False)
    return project


def test_phases_json_gives_three_rows_for_three_done_phases(tmp_path: Path, clock: Clock) -> None:
    _seed_three_done_one_planned(tmp_path, clock)
    result = _metrics(tmp_path, "phases", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    rows = json.loads(result.stdout)
    assert len(rows) == 3
    assert {r["phase"] for r in rows} == {"ph-a", "ph-b", "ph-c"}
    for row in rows:
        assert set(row) >= ROW_FIELDS
    by_phase = {r["phase"]: r for r in rows}
    assert by_phase["ph-b"]["weight"] == "full"
    assert by_phase["ph-c"]["tasks"] == 3
    assert by_phase["ph-a"]["landing_time"] == "2026-11-02T12:00:00+00:00"


def test_record_count_unchanged_after_phases_repairs_and_compare(
    tmp_path: Path, clock: Clock
) -> None:
    project = _seed_three_done_one_planned(tmp_path, clock)
    commands = [
        ("phases",),
        ("phases", "--json"),
        ("repairs", "--since", "2026-10-26"),
        ("compare", "ph-b"),
        ("compare", "ph-b", "--json"),
    ]
    for command in commands:
        records_before = len(project.records())
        token_before = project.change_token()
        result = _metrics(tmp_path, *command)
        assert result.returncode in (0, 1), result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        assert len(project.records()) == records_before, command
        assert project.change_token() == token_before, command


def test_compare_boundary_gives_medians_and_sizes_for_each_side_and_weight(
    tmp_path: Path, clock: Clock
) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    _landed(project, clock, "ph-a", 2, "light", 1)
    _landed(project, clock, "ph-b", 3, "light", 3)
    _landed(project, clock, "ph-edge", 5, "full", 2)
    _landed(project, clock, "ph-c", 7, "light", 4)
    _landed(project, clock, "ph-d", 8, "full", 6)
    _landed(project, clock, "ph-e", 9, "full", 8)
    _specification(project, "ph-e", "ef")

    result = _metrics(tmp_path, "compare", "ph-edge", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["boundary"] == "ph-edge"
    before, after = data["sides"]["before"], data["sides"]["after"]
    assert before["phases"] == 2
    assert set(before["weights"]) == {"light"}
    assert before["weights"]["light"]["columns"]["tasks"] == {"median": 2, "n": 2}
    assert after["phases"] == 3
    assert after["weights"]["light"]["columns"]["tasks"] == {"median": 4, "n": 1}
    assert after["weights"]["full"]["columns"]["tasks"] == {"median": 7, "n": 2}

    text = _metrics(tmp_path, "compare", "ph-edge")
    assert text.returncode == 0, text.stdout + text.stderr
    assert "before" in text.stdout and "after" in text.stdout
    assert not RANKING_WORDS.search(text.stdout)
    assert not RANKING_WORDS.search(result.stdout)
