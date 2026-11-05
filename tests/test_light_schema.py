from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.validation import ValidationError


def test_light_phase_accepts_a_multi_requirement_acceptance(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    create(
        project,
        "score:phase",
        "light-one",
        {"title": "Light", "ordinal": 2, "effort": "alpha", "weight": "light"},
    )
    create(
        project,
        "score:acceptance",
        "light-one",
        {
            "method": "check",
            "phase": "light-one",
            "effort": "alpha",
            "verify_command": "true",
            "requirements": ["R1", "R2"],
        },
    )
    assert project.validate() == []


def test_phase_weight_rejects_an_unknown_value(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    with pytest.raises(ValidationError):
        create(
            project,
            "score:phase",
            "odd",
            {"title": "Odd", "ordinal": 2, "effort": "alpha", "weight": "medium"},
        )
