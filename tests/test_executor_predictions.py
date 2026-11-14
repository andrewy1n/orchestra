from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canon_support import create, make_project, seed_effort

from orchestra import views
from orchestra.canon.project import Project
from orchestra.canon.project_config import ProjectConfigError


def _task(project: Project, subject: str, **extra: object):
    payload = {
        "title": subject,
        "phase": "p1",
        "kind": "deliver",
        "effort": "alpha",
        "assignee": "",
        **extra,
    }
    return create(project, "score:work-item", subject, payload)


def _config(project: Project, budget: int = 15) -> None:
    source = Path(__file__).resolve().parents[1] / "orchestra.toml"
    text = source.read_text(encoding="utf-8")
    project.project_root.joinpath("orchestra.toml").write_text(
        f"{text}\n[execute]\nsmall_wave_budget_minutes = {budget}\n", encoding="utf-8"
    )


def _plan(project: Project) -> str:
    return views.render_view(
        views.PLAN, views.load_records(project), project_root=project.project_root
    )


@pytest.fixture
def project(tmp_path: Path) -> Project:
    result = make_project(tmp_path / "repo")
    seed_effort(result, "alpha")
    _config(result)
    return result


def test_plan_predicts_executor_for_tasks_in_same_wave(project: Project) -> None:
    _task(project, "small-a", size="XS", estimate_minutes=4)
    _task(project, "small-b", size="S", estimate_minutes=6)
    _task(project, "large", size="L", estimate_minutes=20, depends_on=["small-a"])

    text = _plan(project)

    assert "**small-a**: small-a; p1; deliver; alpha; executor: predicted inline" in text
    assert "**small-b**: small-b; p1; deliver; alpha; executor: predicted inline" in text
    assert "**large**: large; p1; deliver; alpha; executor: predicted subagent" in text


def test_plan_uses_configured_budget_and_missing_estimate_upper_bound(project: Project) -> None:
    _config(project, budget=8)
    _task(project, "small-a", size="XS", estimate_minutes=4)
    _task(project, "small-b", size="S")

    text = _plan(project)

    assert "**small-a**: small-a; p1; deliver; alpha; executor: predicted subagent" in text
    assert "**small-b**: small-b; p1; deliver; alpha; executor: predicted subagent" in text


def test_plan_uses_dispatched_assignee_before_override(project: Project) -> None:
    task = _task(project, "dispatched", size="XS", executor="inline")
    project.supersede(
        task["id"],
        payload={
            "title": "dispatched",
            "phase": "p1",
            "kind": "deliver",
            "effort": "alpha",
            "assignee": "subagent",
            "size": "XS",
            "executor": "inline",
        },
    )

    assert "executor: subagent" in _plan(project)
    assert "executor: predicted" not in _plan(project)


def test_plan_ignores_historical_assignee_and_honors_override(project: Project) -> None:
    _task(project, "historical", size="L", assignee="agent-7", executor="inline")

    text = _plan(project)

    assert "executor: inline" in text
    assert "executor: predicted" not in text


def test_plan_reloads_predictions_after_wave_membership_changes(project: Project) -> None:
    _task(project, "first", size="XS", estimate_minutes=4)
    _task(project, "second", size="XS", estimate_minutes=4)
    assert "executor: predicted inline" in _plan(project)

    _task(project, "third", size="XS", estimate_minutes=10)

    assert "executor: predicted subagent" in _plan(project)


def test_plan_reports_missing_project_config(project: Project) -> None:
    project.project_root.joinpath("orchestra.toml").unlink()
    _task(project, "small", size="XS")

    with pytest.raises(ProjectConfigError, match="required project config is missing"):
        _plan(project)
