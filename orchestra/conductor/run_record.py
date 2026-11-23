from __future__ import annotations

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.facts.view_facts import RUN_TYPE


def resolve_run(project: Project, subject: str) -> Record:
    return project.resolve(RUN_TYPE, subject)
