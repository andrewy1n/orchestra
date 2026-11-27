"""Build the phase-end reviewer brief from the store and the phase diff."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.verification.review import reviewer

ArchitectureReview = Callable[[Sequence[Record], Path, str, str, str], str]


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
    project: Project,
    work: Path,
    *,
    base: str,
    phase_head: str,
    phase: str | None,
    suite_refusal: str,
    architecture_review: ArchitectureReview,
) -> str:
    if suite_refusal:
        raise RuntimeError(suite_refusal)
    records = load_review_records(project)
    phase_diff = reviewer.git_phase_diff(work, base=base, phase_head=phase_head)
    brief = reviewer.build_reviewer_brief(
        records=records,
        phase_diff=phase_diff,
        base=base,
        phase_head=phase_head,
        phase=phase,
    )
    if phase is None:
        return brief
    architecture = architecture_review(project.records(), work, phase, base, phase_head)
    return f"{brief.rstrip()}\n\n{architecture}" if architecture else brief
