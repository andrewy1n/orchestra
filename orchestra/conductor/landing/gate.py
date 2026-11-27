"""Phase gate terms behind `orchestra gate` and the gate step of `orchestra land`.

The gate binds to the reviewed revision: the revision of the latest review
check-run for the phase. Terms bound to the head compare against it. The head
worktree is the caller's worktree when it passes one; otherwise it is the
Landing worktree when that exists (the phase body names a `Worktree`, or
`<Repo>/.worktrees/<phase>` exists). Its HEAD must equal or descend from the
reviewed revision, and the commits after it may touch only `.canon/`. The suite
policy comes from the caller's worktree's `orchestra.toml` when it passes one,
else from the store root. With no review check-run, no term bound to the head
can hold.

Each term is one line of the "Phase gate" list in verify's phase-end.md.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.landing.landing import LandingPlace, phase_place
from orchestra.conductor.verification.evidence import head_evidence
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex
from orchestra.conductor.verification.suite import suite
from orchestra.conductor.verification.suite.suite import SuitePolicy
from orchestra.score.lookups import closing_work_item
from orchestra.score.planning.phase import Phase, current_phase_model
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    is_signed,
    latest_manual_check,
    phase_blockers,
)
from orchestra.tools import Git
from orchestra.tools.errors import ToolError

METADATA_DIR = ".canon/"


@dataclass(frozen=True)
class Term:
    name: str
    holds: bool
    detail: str = ""


def _differing_from_base(git: Git, head: str, base: str, paths: list[str]) -> list[str]:
    merge_base = git.run("merge-base", head, base)
    if merge_base.returncode != 0:
        return paths
    fork = merge_base.stdout.strip()
    if fork == head:
        return paths
    diff = git.run("diff", "--name-only", "--no-renames", "-z", f"{fork}..{head}")
    if diff.returncode != 0:
        return paths
    differing = set(diff.stdout.split("\0"))
    return [path for path in paths if path in differing]


def _descent_term(
    worktree: Path, reviewed: str, git_at: Callable[[Path], Git] = Git, base: str = ""
) -> Term:
    name = "head-descends-from-review"
    if not reviewed:
        return Term(name, False, "no review check-run")
    try:
        head = git_at(worktree).head()
    except (OSError, RuntimeError) as exc:
        return Term(name, False, f"cannot resolve the worktree HEAD: {exc}")
    git = git_at(worktree)
    try:
        descends = git.is_ancestor(reviewed, head)
    except ToolError as error:
        detail = error.stderr.strip() or str(error)
        return Term(name, False, f"{' '.join(error.argv)} failed: {detail}")
    if not descends:
        return Term(name, False, f"worktree HEAD {head} does not descend from {reviewed}")
    diff = git.run("diff", "--name-only", "--no-renames", "-z", f"{reviewed}..{head}")
    if diff.returncode != 0:
        return Term(name, False, f"git diff {reviewed}..{head} failed")
    changed = [path for path in diff.stdout.split("\0") if path]
    other = [path for path in changed if not path.startswith(METADATA_DIR)]
    if other and base:
        other = _differing_from_base(git, head, base, other)
    if other:
        return Term(name, False, f"paths changed after review outside .canon/: {', '.join(other)}")
    return Term(name, True)


def _str(record: Record, key: str) -> str:
    value = record["payload"].get(key)
    return value if isinstance(value, str) else ""


def _acceptance_terms(acceptance: Record, index: EvidenceIndex, head: str) -> list[Term]:
    name = acceptance["subject"]
    latest = head_evidence.acceptance_latest(index, acceptance, None)
    terms = [Term(f"acceptance-passes:{name}", latest.holds, latest.reason)]
    if _str(acceptance, "method") != "manual":
        at_head = head_evidence.acceptance_runner_at_head(index, acceptance, head)
        terms.append(Term(f"acceptance-runner-at-head:{name}", at_head.holds, at_head.reason))
    return terms


def gate_terms(
    project: Project,
    phase_slug: str,
    *,
    head_worktree: Path | None = None,
) -> list[Term]:
    """Every phase gate term for the phase, held or not.

    Raises LookupError when the store has no such phase.
    """
    store = project.project_root
    records = project.records()
    phase = current_phase_model(phase_slug, records)
    if phase is None:
        raise LookupError(f"phase {phase_slug!r} not found")
    place = phase_place(phase, store)
    policy = suite.load_suite_policy(head_worktree if head_worktree is not None else store)
    return gate_terms_for(records, phase, place, policy, head_worktree=head_worktree)


def gate_terms_for(
    records: list[Record],
    phase: Phase,
    place: LandingPlace,
    policy: SuitePolicy,
    *,
    head_worktree: Path | None = None,
    git_at: Callable[[Path], Git] = Git,
) -> list[Term]:
    """Every phase gate term for a phase over an in-memory record snapshot."""
    phase_slug = phase.subject
    effort = phase.effort

    def of_type(record_type: str) -> list[Record]:
        return [r for r in records if r["record_type"] == record_type]

    acceptances = [
        r
        for r in of_type("score:acceptance")
        if _str(r, "phase") == phase_slug and r["lifecycle_state"] == "active"
    ]
    index = EvidenceIndex(records)
    latest_review = head_evidence.latest_review(index, phase_slug, effort)
    head = _str(latest_review, "revision") if latest_review else ""

    terms: list[Term] = []

    verification = closing_work_item(phase_slug, records)
    verified = verification is not None and verification["lifecycle_state"] == "done"
    if verification is None:
        detail = "no verification task"
    elif verified:
        detail = ""
    else:
        detail = "verification task is not done"
    terms.append(Term("verification-task-done", verified, detail))

    for acceptance in acceptances:
        terms.extend(_acceptance_terms(acceptance, index, head))

    for acceptance in acceptances:
        manual = latest_manual_check(acceptance, records)
        if manual is not None:
            signed = is_signed(manual)
            terms.append(
                Term(
                    f"manual-check-signed:{acceptance['subject']}",
                    signed,
                    "" if signed else "latest manual check-run has no signed_by",
                )
            )

    review = head_evidence.review_at_head(index, phase_slug, effort, head)
    terms.append(Term("review-at-head", review.holds, review.reason))

    if head_worktree is not None:
        terms.append(_descent_term(head_worktree, head, git_at, place.base))
    else:
        if place.worktree.is_dir():
            terms.append(_descent_term(place.worktree, head, git_at, place.base))

    if policy.gate == "required" and policy.mode not in ("none", ""):
        at_head = head_evidence.suite_at_head(index, phase_slug, head)
        terms.append(Term("suite-at-head", at_head.holds, at_head.reason))

    try:
        blockers = phase_blockers(records, phase_slug)
    except WorkflowBlockerError as exc:
        raise LookupError(str(exc)) from exc
    if blockers:
        for blocker in blockers:
            record = blocker.record
            if record["record_type"] == "tuner:finding":
                name = f"finding-needs-human:{record['subject']}"
                detail = _str(record, "claim")
            else:
                name = f"question-needs-human:{record['subject']}"
                detail = _str(record, "scope")
            terms.append(
                Term(
                    name,
                    False,
                    detail,
                )
            )
    else:
        terms.append(Term("no-human-findings", True))
    return terms


def missing_terms(terms: Sequence[Term]) -> list[Term]:
    return [term for term in terms if not term.holds]


def format_missing(terms: Sequence[Term]) -> list[str]:
    return [f"missing {t.name}" + (f": {t.detail}" if t.detail else "") for t in terms]
