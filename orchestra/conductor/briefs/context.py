from __future__ import annotations

from orchestra.canon.project import Project
from orchestra.canon.project_config import ProjectConfigError, load_project_config
from orchestra.conductor.briefs.render import BriefContext
from orchestra.conductor.workflow import step_stage


def _adapter(project: Project) -> str:
    try:
        config = load_project_config(project.project_root)
    except ProjectConfigError:
        return ""
    return config.land_adapter if config.land_configured else ""


def _text(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def brief_context(project: Project, phase: str, step: str) -> BriefContext:
    record = project.resolve("score:phase", phase)
    stage = step_stage(project, project.records(), phase, step)
    payload = record["payload"]
    return BriefContext(
        step=step,
        phase=phase,
        effort=_text(payload.get("effort"), ""),
        stage=stage,
        adapter=_adapter(project),
        weight=_text(payload.get("weight"), "full"),
    )
