from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project

PHASE = "analysis-executor"


def _repo(tmp_path: Path, budget: int) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\ntask = ["unit"]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", '
        '"--junitxml={report}"]\n\n'
        f"[execute]\nsmall_wave_budget_minutes = {budget}\n",
        encoding="utf-8",
    )
    create(project, "score:effort", "effort", {"goal": "test", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Analysis executor", "ordinal": 1, "effort": "effort", "weight": "light"},
        "## Problem\n\nTest analysis.\n\n## Approach\n\nTest analysis.\n\n"
        "## Exit criteria\n\nAnalysis passes.\n\n## Requirements\n\n"
        "R1: The analyzer reports executor overrides.\n",
    )
    return project, tmp_path


def _item(
    project: Project,
    subject: str,
    *,
    executor: str | None = None,
    size: str = "XS",
    estimate_minutes: int = 8,
    depends_on: list[str] | None = None,
) -> None:
    payload: dict[str, object] = {
        "title": subject,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": "effort",
        "size": size,
        "estimate_minutes": estimate_minutes,
        "requirements": ["R1"],
    }
    if executor is not None:
        payload["executor"] = executor
    if depends_on is not None:
        payload["depends_on"] = depends_on
    create(project, "score:work-item", subject, payload)


def _analyze(repo: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "analyze", PHASE, "--json"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


def _codes(result: subprocess.CompletedProcess[str]) -> set[str]:
    return {finding["code"] for finding in json.loads(result.stdout)["findings"]}


@pytest.mark.parametrize(("budget", "warns"), [(15, False), (16, True)])
def test_cli_derives_override_against_configured_wave_budget(
    tmp_path: Path, budget: int, warns: bool
) -> None:
    project, repo = _repo(tmp_path, budget=budget)
    _item(project, "first", executor="subagent")
    _item(project, "second")
    create(
        project,
        "score:acceptance",
        "R1",
        {
            "phase": PHASE,
            "effort": "effort",
            "requirement": "R1",
            "method": "tdd",
            "verify_command": "true",
        },
    )

    result = _analyze(repo)

    assert result.returncode == 0, result.stderr
    assert ("executor-override-differs" in _codes(result)) is warns


def test_cli_solo_subagent_task_has_no_retired_warning(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path, budget=15)
    _item(project, "solo", executor="subagent", size="S", estimate_minutes=10)
    create(
        project,
        "score:acceptance",
        "R1",
        {
            "phase": PHASE,
            "effort": "effort",
            "requirement": "R1",
            "method": "tdd",
            "verify_command": "true",
        },
    )

    result = _analyze(repo)

    assert result.returncode == 0, result.stderr
    assert "small-subagent-solo-wave" not in _codes(result)
