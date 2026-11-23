from __future__ import annotations

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.conductor.briefs.render import BriefContext
from orchestra.conductor.phases.workflow.workflow import step_stage
from orchestra.score.planning.phase import current_phase_model


def _adapter(project: Project) -> str:
    config = load_project_config(project.project_root)
    return config.land_adapter if config.land_configured else ""


def brief_context(project: Project, phase: str, step: str) -> BriefContext:
    records = project.records()
    model = current_phase_model(phase, records)
    if model is None:
        raise StoreError(f"unknown record: no score:phase with subject {phase!r}")
    stage = step_stage(project, records, phase, step)
    return BriefContext(
        step=step,
        phase=phase,
        effort=model.effort,
        stage=stage,
        adapter=_adapter(project),
        weight=model.weight or "full",
    )
