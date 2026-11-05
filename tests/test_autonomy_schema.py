from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.validation import ValidationError


@pytest.mark.parametrize("level", ["gated", "auto-plan", "auto-phases"])
def test_r01_effort_accepts_each_autonomy_level(tmp_path: Path, level: str) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "e", {"goal": "g", "kind": "deliver", "autonomy": level})
    assert project.validate() == []


def test_r01_effort_without_autonomy_is_valid(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "e", {"goal": "g", "kind": "deliver"})
    assert project.validate() == []


def test_r01_effort_rejects_an_unknown_autonomy_level(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    with pytest.raises(ValidationError):
        create(project, "score:effort", "e", {"goal": "g", "kind": "deliver", "autonomy": "yolo"})
