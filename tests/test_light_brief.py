from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project
from test_brief_quotes import _orientation, _record, _work_item

from orchestra import views

LIGHT_BODY = "## Requirements\n\nR1: Light wording of the first requirement.\nR2: Second.\n"


def test_orientation_quotes_a_light_phase_requirement_from_the_phase_body() -> None:
    phase = _record("score:phase", "p1", {"weight": "light"}, LIGHT_BODY, "in_progress")
    block = _orientation(views.render_brief("build-it", [_work_item(requirements=["R1"]), phase]))
    quoted = block.split("### Requirements")[1]
    assert "- R1: Light wording of the first requirement." in quoted
    assert "R2" not in quoted


def test_orientation_keeps_the_specification_for_a_full_phase() -> None:
    phase = _record("score:phase", "p1", {"weight": "full"}, LIGHT_BODY, "in_progress")
    spec = _record(
        "score:specification",
        "p1",
        {"phase": "p1", "requirements": ["R1"]},
        "## Requirements\n\nR1: Spec wording.\n",
    )
    block = _orientation(
        views.render_brief("build-it", [_work_item(requirements=["R1"]), phase, spec])
    )
    assert "- R1: Spec wording." in block


def test_cli_brief_quotes_a_light_phase_requirement(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "alpha", {"goal": "G", "kind": "deliver"})
    create(
        project,
        "score:phase",
        "p1",
        {"title": "P", "ordinal": 1, "effort": "alpha", "weight": "light"},
        "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n" + LIGHT_BODY,
    )
    create(
        project,
        "score:work-item",
        "build-it",
        {
            "title": "Build",
            "phase": "p1",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "requirements": ["R1"],
        },
        "## Description\n\nNo ids here.\n\n## Approach\n\nDo it.",
    )
    env = dict(os.environ, PYTHONPATH=str(REPO))
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "brief", "build-it"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "- R1: Light wording of the first requirement." in result.stdout
