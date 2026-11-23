"""Land a task and decide its closure in one operation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.project import Project
from orchestra.conductor import land_task, task_close
from orchestra.conductor.verification.requirements import requirement_status, verified_requirements


@dataclass(frozen=True)
class TaskLanding:
    landed: land_task.LandedTask
    closure: task_close.Closure


def land_and_close(project: Project, repo: Path, task: str, evidence_path: Path) -> TaskLanding:
    landed = land_task.land(project, repo, task, evidence_path)
    statuses = requirement_status(project.records(), landed.phase, head=landed.revision)
    closure = task_close.close(project, landed, verified_requirements(statuses))
    return TaskLanding(landed, closure)
