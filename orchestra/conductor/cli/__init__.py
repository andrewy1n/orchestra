"""CLI wiring for the conductor verbs."""

from __future__ import annotations

from dataclasses import dataclass

from orchestra.conductor.cli import (
    check,
    close,
    land,
    merge_evidence,
    phase_commands,
    suite_commands,
    wave_commands,
    workflow_commands,
)
from orchestra.conductor.cli.wave_commands import BriefRenderer
from orchestra.conductor.phases.progress.close import ReconcileArchitecture
from orchestra.conductor.phases.workflow.workflow import ProjectContext
from orchestra.conductor.verification.check import ProposedConstraintReader
from orchestra.conductor.verification.review.review_brief import ArchitectureReview
from orchestra.tools.command_kit import Command

__all__ = ["BriefRenderer", "commands"]


@dataclass(frozen=True)
class ArchitectureChanges:
    review: ArchitectureReview
    proposed_constraint: ProposedConstraintReader
    reconcile: ReconcileArchitecture


def commands(
    *,
    render_brief: BriefRenderer,
    project_context: ProjectContext,
    architecture: ArchitectureChanges,
) -> list[Command]:
    return [
        *check.commands(architecture.proposed_constraint),
        *workflow_commands.commands(project_context),
        *wave_commands.commands(render_brief),
        *land.commands(),
        *merge_evidence.commands(),
        *close.commands(architecture.reconcile),
        *phase_commands.commands(architecture.review),
        *suite_commands.commands(),
    ]
