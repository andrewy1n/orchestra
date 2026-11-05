from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort


@pytest.mark.parametrize(
    ("record_type", "payload"),
    [
        (
            "score:work-item",
            {
                "title": "Tweak",
                "phase": "",
                "kind": "incidental",
                "assignee": "",
                "effort": "alpha",
            },
        ),
        (
            "score:acceptance",
            {"method": "check", "phase": "", "effort": "alpha", "verify_command": "true"},
        ),
    ],
)
def test_incidental_record_may_have_empty_phase(
    tmp_path: Path, record_type: str, payload: dict[str, str]
) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    create(project, record_type, "incidental-one", payload)
    errors = project.validate()
    assert errors == []
