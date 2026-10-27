"""Evidence kinds and the runner templates each kind may be witnessed under."""

from __future__ import annotations

from typing import Sequence

from affidavit.manifest import DEFAULT_RUNNER

KINDS = ("unit", "integration", "interaction")
DEFAULT_KIND = "unit"

TEMPLATES: dict[str, tuple[str, ...]] = {
    "unit": DEFAULT_RUNNER,
    "interaction": (
        "env",
        "AFF_EVIDENCE_KIND=interaction",
        "python3",
        "-m",
        "pytest",
        "-o",
        "junit_family=xunit1",
        "{tests}",
        "--junitxml={report}",
    ),
}


def kind_allows_runner(kind: str, runner: Sequence[str]) -> bool:
    """Only ``interaction`` restricts the runner, to the interaction template."""
    if kind == "interaction":
        return tuple(runner) == TEMPLATES["interaction"]
    return True
