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
from orchestra.tools.command_kit import Command

__all__ = ["BriefRenderer", "commands"]


def commands(*, render_brief: BriefRenderer) -> list[Command]:
    return [
        *check.commands(),
        *workflow_commands.commands(),
        *wave_commands.commands(render_brief),
        *land.commands(),
        *merge_evidence.commands(),
        *close.commands(),
        *phase_commands.commands(),
        *suite_commands.commands(),
    ]
