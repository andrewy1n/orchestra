"""Build the phase-end reviewer brief from the store and the phase diff."""

from __future__ import annotations

from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.verification.review import repeat_review, reviewer
from orchestra.tools import Git


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
) -> str:
    if suite_refusal:
        raise RuntimeError(suite_refusal)
    records = load_review_records(project)
    phase_diff = reviewer.git_phase_diff(work, base=base, phase_head=phase_head)
    text = reviewer.build_reviewer_brief(
        records=records,
        phase_diff=phase_diff,
        base=base,
        phase_head=phase_head,
        phase=phase,
    )
    if phase is None:
        return text
    prior = repeat_review.prior_failed_review(project, phase)
    if prior is None:
        return text
    return text + _repeat_sections(project, work, prior, phase=phase, phase_head=phase_head)


def _repeat_sections(
    project: Project, work: Path, prior: Record, *, phase: str, phase_head: str
) -> str:
    reviewed = str(record_payload(prior).get("revision") or "")
    result = Git(work).run("diff", f"{reviewed}..{phase_head}")
    if result.returncode != 0:
        raise RuntimeError(
            f"cannot read the repair diff {reviewed}..{phase_head}: {result.stderr.strip()}"
        )
    repair_diff = result.stdout
    changed = repeat_review.changed_paths(repair_diff)
    findings = [str(prior.get("body") or "").strip()]
    findings.extend(
        str(row.get("body") or record_payload(row).get("claim") or "").strip()
        for row in repeat_review.prior_findings(project, phase)
    )
    findings = list(dict.fromkeys(text for text in findings if text))
    callers = repeat_review.affected_callers(work, changed)
    lines = ["## Prior review", "", f"Reviewed revision: `{reviewed}`", ""]
    lines += [*findings, ""] if findings else []
    lines += ["## Repair diff", "", f"`git diff {reviewed}..{phase_head}`", ""]
    lines += ["```diff", repair_diff.rstrip() or "(empty)", "```", ""]
    lines += ["## Affected callers", ""]
    lines += [f"- {path}" for path in callers] or ["(none)"]
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
