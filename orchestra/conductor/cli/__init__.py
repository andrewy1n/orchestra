"""CLI wiring for the conductor verbs."""

from __future__ import annotations

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
from orchestra.conductor.verification.check import ProposedConstraintReader
from orchestra.conductor.verification.review.review_brief import ArchitectureReview
from orchestra.tools.command_kit import Command

__all__ = ["BriefRenderer", "commands"]


def commands(
    *,
    render_brief: BriefRenderer,
    architecture_review: ArchitectureReview | None = None,
    proposed_constraint: ProposedConstraintReader | None = None,
    reconcile_architecture: ReconcileArchitecture | None = None,
) -> list[Command]:
    return [
        *check.commands(proposed_constraint),
        *workflow_commands.commands(),
        *wave_commands.commands(render_brief),
        *land.commands(),
        *merge_evidence.commands(),
        *close.commands(reconcile_architecture),
        *phase_commands.commands(architecture_review),
        *suite_commands.commands(),
    ]
