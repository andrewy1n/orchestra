"""Build the phase-end reviewer brief from the store and the phase diff."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor import reviewer, suite
from orchestra.tools.git import Git


@dataclass(frozen=True)
class ReviewBrief:
    refusal: str
    text: str


def suite_refusal(project: Project, work: Path, phase: str, phase_head: str) -> str:
    policy = suite.load_suite_policy(work)
    if not policy.run_locally:
        return ""
    resolved = Git(work).resolve(phase_head)
    if resolved is None:
        raise RuntimeError(f"cannot resolve {phase_head}")
    check_runs = [row for row in project.list("tuner:check-run") if isinstance(row, dict)]  # pyright: ignore[reportUnnecessaryIsInstance]
    return suite.suite_ready_for_review(policy, check_runs, phase_slug=phase, phase_head=resolved)


def load_review_records(project: Project) -> list[Record]:
    records: list[Record] = []
    failures: list[str] = []
    for kind in sorted(reviewer.ALLOWED_KINDS):
        record_type = f"score:{kind}"
        try:
            rows = project.list(record_type)
        except StoreError as exc:
            failures.append(f"{record_type}: {exc}")
            continue
        records.extend(row for row in rows if isinstance(row, dict))  # pyright: ignore[reportUnnecessaryIsInstance]
    if failures:
        raise RuntimeError("; ".join(failures))
    return records


def build_review_brief(
    project: Project, work: Path, *, base: str, phase_head: str, phase: str | None
) -> ReviewBrief:
    if phase:
        refusal = suite_refusal(project, work, phase, phase_head)
        if refusal:
            return ReviewBrief(refusal=refusal, text="")
    records = load_review_records(project)
    phase_diff = reviewer.git_phase_diff(work, base=base, phase_head=phase_head)
    text = reviewer.build_reviewer_brief(
        records=records,
        phase_diff=phase_diff,
        base=base,
        phase_head=phase_head,
        phase=phase,
    )
    return ReviewBrief(refusal="", text=text)
