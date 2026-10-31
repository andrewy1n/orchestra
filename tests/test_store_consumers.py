from pathlib import Path
from typing import Any

import pytest

from canon_support import make_project
from orchestra.canon.project import Project
from orchestra.canon.errors import StoreError
from orchestra.conductor.suite import load_suite_policy


def test_suite_policy_reads_project_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = make_project(tmp_path / "repo")
    calls: list[Project] = []

    def config(target: Project) -> dict[str, Any]:
        calls.append(target)
        return {
            "settings": {
                "conductor": {
                    "phase_gate": {
                        "suite": {
                            "mode": "full",
                            "command": "pytest -q",
                            "gate": "advisory",
                        }
                    }
                }
            }
        }

    monkeypatch.setattr(Project, "config", config)
    policy = load_suite_policy(project.project_root)
    assert (policy.mode, policy.command, policy.gate) == ("full", "pytest -q", "advisory")
    assert calls == [project]
    assert policy.source_path == str(project.store_path)


def test_suite_policy_defaults_when_project_config_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = make_project(tmp_path / "repo")

    def config(target: Project) -> dict[str, Any]:
        raise StoreError("backend unavailable")

    monkeypatch.setattr(Project, "config", config)
    policy = load_suite_policy(project.project_root)
    assert (policy.mode, policy.command, policy.gate) == ("none", "", "required")
    assert policy.source_path is None
