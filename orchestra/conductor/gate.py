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

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.conductor import head_evidence, suite
from orchestra.conductor.check import git_head
from orchestra.conductor.head_evidence import EvidenceIndex
from orchestra.score.workflow_blockers import WorkflowBlockerError, phase_blockers
from orchestra.tools import Git

METADATA_DIR = ".canon/"
LIVE_WORK_ITEM_STATES = frozenset({"planned", "in_progress", "done"})

_LANDING_HEADING = re.compile(r"^##\s+Landing\s*$")
_NEXT_HEADING = re.compile(r"^##\s+")
_LANDING_LINE = re.compile(r"^(?:[-*]\s+)?(repo|worktree)\s*:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Term:
    name: str
    holds: bool
    detail: str = ""


@dataclass(frozen=True)
class LandingSpec:
    present: bool = False
    repo: str = ""
    worktree: str = ""


def _unwrap(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def parse_landing(body: str) -> LandingSpec:
    """Read `Repo:` and `Worktree:` lines from the `## Landing` section."""
    inside = False
    found = False
    values: dict[str, str] = {}
    for line in body.splitlines():
        if _LANDING_HEADING.match(line):
            inside = True
            found = True
            continue
        if inside and _NEXT_HEADING.match(line):
            break
        if not inside:
            continue
        match = _LANDING_LINE.match(line.strip())
        if match:
            values.setdefault(match.group(1).lower(), _unwrap(match.group(2)))
    return LandingSpec(
        present=found,
        repo=values.get("repo", ""),
        worktree=values.get("worktree", ""),
    )


def _resolve_path(store: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else store / path


def landing_repo(store: Path, landing: LandingSpec) -> Path:
    if not landing.repo:
        return store
    return _resolve_path(store, landing.repo)


def landing_worktree(store: Path, phase_slug: str, landing: LandingSpec) -> Path:
    if landing.worktree:
        return _resolve_path(store, landing.worktree)
    return landing_repo(store, landing) / ".worktrees" / phase_slug


def _descent_term(worktree: Path, reviewed: str) -> Term:
    name = "head-descends-from-review"
    if not reviewed:
        return Term(name, False, "no review check-run")
    try:
        head = git_head(worktree)
    except (OSError, RuntimeError) as exc:
        return Term(name, False, f"cannot resolve the worktree HEAD: {exc}")
    git = Git(worktree)
    if git.run("merge-base", "--is-ancestor", reviewed, head).returncode != 0:
        return Term(name, False, f"worktree HEAD {head} does not descend from {reviewed}")
    diff = git.run("diff", "--name-only", "--no-renames", "-z", f"{reviewed}..{head}")
    if diff.returncode != 0:
        return Term(name, False, f"git diff {reviewed}..{head} failed")
    changed = [path for path in diff.stdout.split("\0") if path]
    other = [path for path in changed if not path.startswith(METADATA_DIR)]
    if other:
        return Term(name, False, f"paths changed after review outside .canon/: {', '.join(other)}")
    return Term(name, True)


def _str(record: Record, key: str) -> str:
    value = record["payload"].get(key)
    return value if isinstance(value, str) else ""


def _depends_on(record: Record) -> set[str]:
    raw = record["payload"].get("depends_on")
    if not isinstance(raw, list):
        return set()
    return {item for item in raw if isinstance(item, str)}


def _verification_items(items: Sequence[Record]) -> list[Record]:
    live = [item for item in items if item["lifecycle_state"] in LIVE_WORK_ITEM_STATES]
    found: list[Record] = []
    for item in live:
        others = [other for other in live if other["id"] != item["id"]]
        deps = _depends_on(item)
        if others and all(o["subject"] in deps or o["id"] in deps for o in others):
            found.append(item)
    return found


def _acceptance_terms(acceptance: Record, index: EvidenceIndex, head: str) -> list[Term]:
    name = acceptance["subject"]
    latest = head_evidence.acceptance_latest(index, acceptance, None)
    terms = [Term(f"acceptance-passes:{name}", latest.holds, latest.reason)]
    if _str(acceptance, "method") != "manual":
        at_head = head_evidence.acceptance_runner_at_head(index, acceptance, head)
        terms.append(Term(f"acceptance-runner-at-head:{name}", at_head.holds, at_head.reason))
    return terms


def gate_terms(
    store: Path,
    phase_slug: str,
    *,
    store_dir: Path | None = None,
    head_worktree: Path | None = None,
) -> list[Term]:
    """Every phase gate term for the phase, held or not.

    Raises LookupError when the store has no such phase.
    """
    records = open_store(store, store=store_dir).records()
    phase = next(
        (
            r
            for r in records
            if r["record_type"] == "score:phase"
            and r["subject"] == phase_slug
            and r["lifecycle_state"] != "superseded"
        ),
        None,
    )
    if phase is None:
        raise LookupError(f"phase {phase_slug!r} not found")
    effort = _str(phase, "effort")
    landing = parse_landing(phase.get("body", ""))

    def of_type(record_type: str) -> list[Record]:
        return [r for r in records if r["record_type"] == record_type]

    items = [r for r in of_type("score:work-item") if _str(r, "phase") == phase_slug]
    acceptances = [
        r
        for r in of_type("score:acceptance")
        if _str(r, "phase") == phase_slug and r["lifecycle_state"] == "active"
    ]
    index = EvidenceIndex(records)
    latest_review = head_evidence.latest_review(index, phase_slug, effort)
    head = _str(latest_review, "revision") if latest_review else ""

    terms: list[Term] = []

    verification = _verification_items(items)
    verified = bool(verification) and all(i["lifecycle_state"] == "done" for i in verification)
    if not verification:
        detail = "no verification task"
    elif verified:
        detail = ""
    else:
        detail = "verification task is not done"
    terms.append(Term("verification-task-done", verified, detail))

    for acceptance in acceptances:
        terms.extend(_acceptance_terms(acceptance, index, head))

    for acceptance in acceptances:
        manual = head_evidence.latest(
            [
                r
                for r in head_evidence.acceptance_runs(index, acceptance)
                if _str(r, "method") == "manual"
            ]
        )
        if manual:
            signed = bool(_str(manual, "signed_by").strip())
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
        terms.append(_descent_term(head_worktree, head))
    else:
        worktree = landing_worktree(store, phase_slug, landing)
        if worktree.is_dir():
            terms.append(_descent_term(worktree, head))

    policy = suite.load_suite_policy(head_worktree if head_worktree is not None else store)
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
