"""Build the phase-end reviewer brief from the store and the phase diff."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.verification.review import repeat_review, reviewer
from orchestra.tools import Git

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
    if architecture:
        brief = f"{brief.rstrip()}\n\n{architecture}"
    prior = repeat_review.prior_failed_review(project, phase)
    if prior is None:
        return brief
    repeat = _repeat_sections(work, prior, phase_head=phase_head)
    return f"{brief.rstrip()}\n\n{repeat}"


def _repeat_sections(work: Path, prior: Record, *, phase_head: str) -> str:
    reviewed = str(record_payload(prior).get("revision") or "")
    git = Git(work)
    repair = git.run("diff", f"{reviewed}..{phase_head}")
    names = git.run("diff", "--name-only", "--no-renames", f"{reviewed}..{phase_head}")
    for result in (repair, names):
        if result.returncode != 0:
            raise RuntimeError(
                f"cannot read the repair diff {reviewed}..{phase_head}: {result.stderr.strip()}"
            )
    repair_diff = repair.stdout
    changed = [line for line in names.stdout.splitlines() if line]
    findings = str(prior.get("body") or "").strip()
    callers = repeat_review.affected_callers(work, changed)
    lines = ["## Prior review", "", f"Reviewed revision: `{reviewed}`", ""]
    lines += [findings, ""] if findings else []
    lines += ["## Repair diff", "", f"`git diff {reviewed}..{phase_head}`", ""]
    lines += ["```diff", repair_diff.rstrip() or "(empty)", "```", ""]
    lines += ["## Affected callers", ""]
    lines += [f"- {path}" for path in callers] or ["(none)"]
    lines.append("")
    unscanned = repeat_review.unscanned_files(work)
    if unscanned:
        lines += ["## Unscanned files", "", "These Python files could not be read or parsed:", ""]
        lines += [f"- {path}" for path in unscanned]
        lines.append("")
    if repeat_review.needs_expansion(work, changed):
        lines += [
            "## Expanded review",
            "",
            "The repair touches a shared contract, a permission boundary, or integration "
            "behavior. Review the affected callers and the changed contract beyond the "
            "prior findings.",
            "",
        ]
    return "\n".join(lines)
