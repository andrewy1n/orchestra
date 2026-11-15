import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from canon_support import create, make_project, seed_effort

from dashboard.backend.snapshot import load_snapshot
from orchestra import views
from orchestra.canon.project import Project
from orchestra.canon.project_config import ProjectConfigError


def _task(project: Project, subject: str, **extra: object):
    return create(
        project,
        "score:work-item",
        subject,
        {
            "title": subject,
            "phase": "p1",
            "kind": "deliver",
            "effort": "alpha",
            "assignee": "",
            **extra,
        },
    )


def _config(project: Project, budget: int = 15) -> None:
    source = Path(__file__).resolve().parents[2] / "orchestra.toml"
    text = source.read_text(encoding="utf-8")
    project.project_root.joinpath("orchestra.toml").write_text(
        f"{text}\n[execute]\nsmall_wave_budget_minutes = {budget}\n", encoding="utf-8"
    )


@pytest.fixture
def project(tmp_path: Path) -> Project:
    result = make_project(tmp_path / "repo")
    seed_effort(result, "alpha")
    _config(result)
    return result


def _tasks(project: Project):
    effort = next(effort for effort in load_snapshot(project).efforts if effort.effort == "alpha")
    return {task.subject: task for task in effort.tasks}


def test_dashboard_matches_plan_predictions_for_each_phase_wave(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    _task(project, "small-a", size="XS", estimate_minutes=4)
    _task(project, "small-b", size="S", estimate_minutes=6)
    _task(project, "large", size="L", estimate_minutes=20, depends_on=["small-a"])

    snapshot = load_snapshot(project)
    effort = next(effort for effort in snapshot.efforts if effort.effort == "alpha")
    tasks = {task.subject: task for task in effort.tasks}
    monkeypatch.chdir(project.project_root)
    plan = views.render_view(views.PLAN, views.load_records(project))

    assert tasks["small-a"].executor == "inline"
    assert tasks["small-b"].executor == "inline"
    assert tasks["large"].executor == "subagent"
    assert effort.phases[0].elapsed_minutes == 30
    assert "**small-a**: small-a; p1; deliver; alpha; executor: predicted inline" in plan


def test_dashboard_uses_configured_budget_for_missing_estimates(project: Project) -> None:
    _config(project, budget=8)
    _task(project, "small-a", size="XS", estimate_minutes=4)
    _task(project, "small-b", size="S")

    tasks = _tasks(project)
    assert {task.executor for task in tasks.values()} == {"subagent"}
    assert tasks["small-b"].estimate_minutes is None


def test_dashboard_recomputes_prediction_when_wave_membership_changes(project: Project) -> None:
    _task(project, "first", size="XS", estimate_minutes=4)
    _task(project, "second", size="XS", estimate_minutes=4)
    assert {task.executor for task in _tasks(project).values()} == {"inline"}

    _task(project, "third", size="XS", estimate_minutes=10)

    assert {task.executor for task in _tasks(project).values()} == {"subagent"}


def test_dashboard_uses_dispatched_assignee_before_override(project: Project) -> None:
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

    assert _tasks(project)["dispatched"].executor == "subagent"


def test_dashboard_ignores_historical_assignee_and_honors_override(project: Project) -> None:
    _task(project, "historical", size="L", assignee="agent-7", executor="inline")

    assert _tasks(project)["historical"].executor == "inline"


def test_dashboard_reports_missing_project_config(project: Project) -> None:
    project.project_root.joinpath("orchestra.toml").unlink()
    _task(project, "small", size="XS")

    with pytest.raises(ProjectConfigError, match="required project config is missing"):
        load_snapshot(project)
