from __future__ import annotations

from unittest.mock import create_autospec

from orchestra.canon.project import Project
from orchestra.conductor.phases.workflow.run_record import resolve_run


def test_resolve_run_resolves_the_run_record_type() -> None:
    project = create_autospec(Project, instance=True)
    project.resolve.return_value = {"subject": "r1"}
    assert resolve_run(project, "r1") == {"subject": "r1"}
    project.resolve.assert_called_once_with("score:run", "r1")
