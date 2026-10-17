"""Dirty-pass and result-mapping policy for aff check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Result = Literal["pass", "fail", "blocked"]


@dataclass(frozen=True)
class DirtyDecision:
    """How to set revision / diff_sha256 for a recorded check-run."""

    revision: str
    diff_sha256: str | None = None
    refuse: bool = False
    refuse_message: str = ""


def map_process_outcome(
    *,
    exit_code: int | None,
    timed_out: bool = False,
    missing: bool = False,
) -> Result:
    if timed_out or missing:
        return "blocked"
    if exit_code == 0:
        return "pass"
    return "fail"


def dirty_pass_decision(
    *,
    dirty: bool,
    result: Result,
    head: str,
    diff_sha256: str | None,
    allow_dirty: bool,
) -> DirtyDecision:
    """Refuse dirty pass without override; allow dirty fail/blocked; override → dirty+diff."""
    if not dirty:
        return DirtyDecision(revision=head)
    if result == "pass" and not allow_dirty:
        return DirtyDecision(
            revision="dirty",
            diff_sha256=diff_sha256,
            refuse=True,
            refuse_message=(
                "Refusing to record a pass on a dirty tree. "
                "Commit first, or re-run with --allow-dirty "
                "(records revision=dirty and diff_sha256)."
            ),
        )
    return DirtyDecision(revision="dirty", diff_sha256=diff_sha256)


def manual_refuse_message() -> str:
    return (
        "Acceptance method is manual; aff check does not run it. "
        "Record a check-run with method=manual and set signed_by for human sign-off "
        "(see verify-work)."
    )
