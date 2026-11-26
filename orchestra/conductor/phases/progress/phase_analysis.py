"""Run the phase consistency analysis against one store."""

from __future__ import annotations

from pathlib import Path

from orchestra.canon.derive import attach_derived_all
from orchestra.canon.project import Project
from orchestra.canon.project_config import (
    CONFIG_PATH,
    DEFAULT_EXECUTOR_SETTINGS,
    load_project_config,
)
from orchestra.score.lookups import current_phase
from orchestra.score.planning.analyze import Report, analyze_phase


def analyze_in_store(project: Project, root: Path, phase: str, stage: str) -> Report | None:
    """Return the report for `phase`, or None when the store has no such phase."""
    records = project.records()
    records = attach_derived_all(records, project.derived(records))
    settings = DEFAULT_EXECUTOR_SETTINGS
    if stage in ("plan", "close"):
        config_path = root / CONFIG_PATH
        if config_path.exists() or config_path.is_symlink():
            settings = load_project_config(root).executor_settings
    if current_phase(phase, records) is None:
        return None
    return analyze_phase(records, phase, stage, settings)
