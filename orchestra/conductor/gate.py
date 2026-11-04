"""Phase gate terms behind `orchestra gate` and the gate step of `orchestra land`.

The gate binds to the reviewed revision: the revision of the latest review
check-run for the phase. Terms bound to the head compare against it. When the
Landing worktree exists (the phase body names a `Worktree`, or
`<Repo>/.worktrees/<phase>` exists), its HEAD must equal or descend from the
reviewed revision, and the commits after it may touch only `.canon/`. With no
review check-run, no term bound to the head can hold.

Each term is one line of the "Phase gate" list in execute-phase's phase-end.md.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.git_backend import run_git
from orchestra.canon.project import open_store
from orchestra.canon.query import order_by_recorded_at
from orchestra.canon.types import Record
from orchestra.conductor import reviewer, suite
from orchestra.conductor.check import RUNNER, git_head

INACTIVE_FINDING_STATES = frozenset({"refuted", "retracted"})
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_git(cwd, *args, capture_output=True, text=True, check=False)


def _descent_term(worktree: Path, reviewed: str) -> Term:
    name = "head-descends-from-review"
    if not reviewed:
        return Term(name, False, "no review check-run")
    try:
        head = git_head(worktree)
    except (OSError, RuntimeError) as exc:
        return Term(name, False, f"cannot resolve the worktree HEAD: {exc}")
    ancestry = _git(worktree, "merge-base", "--is-ancestor", reviewed, head)
    if ancestry.returncode != 0:
        return Term(name, False, f"worktree HEAD {head} does not descend from {reviewed}")
    diff = _git(worktree, "diff", "--name-only", "--no-renames", "-z", f"{reviewed}..{head}")
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


def _chronological(records: Sequence[Record]) -> list[Record]:
    return order_by_recorded_at(list(records))


def _latest(records: Sequence[Record]) -> Record | None:
    ordered = _chronological(records)
    return ordered[-1] if ordered else None


def _corrected_ids(records: Sequence[Record]) -> set[str]:
    corrected: set[str] = set()
    for record in records:
        corrected.update((record.get("relationships") or {}).get("corrects") or [])
    return corrected


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


def _runs_for(runs: Sequence[Record], acceptance: Record) -> list[Record]:
    keys = {acceptance["id"], acceptance["subject"]}
    return [run for run in runs if _str(run, "criterion_id") in keys]


def _is_review_run(run: Record, phase_slug: str, effort: str) -> bool:
    if _str(run, "method") != "review" or _str(run, "effort") != effort:
        return False
    return phase_slug + "-review" in {_str(run, "criterion_id"), run["subject"]}


def _is_suite_run(run: Record, phase_slug: str) -> bool:
    expected = suite.suite_subject(phase_slug)
    return expected in {_str(run, "criterion_id"), run["subject"]}


def _term_for_acceptance(
    acceptance: Record, runs: Sequence[Record], head: str
) -> tuple[Term, Term | None]:
    name = acceptance["subject"]
    own = _runs_for(runs, acceptance)
    latest = _latest(own)
    if latest is None:
        passes, reason = False, "no check-run"
    else:
        result = _str(latest, "result")
        passes, reason = result == "pass", f"latest check-run result is {result}"
    first = Term(f"acceptance-passes:{name}", passes, "" if passes else reason)
    if _str(acceptance, "method") == "manual":
        return first, None
    at_head = any(
        _str(run, "runner") == RUNNER
        and _str(run, "result") == "pass"
        and reviewer.revision_matches(_str(run, "revision"), head)
        for run in own
    )
    second = Term(
        f"acceptance-runner-at-head:{name}",
        at_head,
        "" if at_head else f"no passing runner check-run at {head or 'unknown head'}",
    )
    return first, second


def gate_terms(store: Path, phase_slug: str, *, store_dir: Path | None = None) -> list[Term]:
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
    corrected = _corrected_ids(records)
    runs = [r for r in of_type("tuner:check-run") if r["id"] not in corrected]
    review_runs = [r for r in runs if _is_review_run(r, phase_slug, effort)]

    latest_review = _latest(review_runs)
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
        first, second = _term_for_acceptance(acceptance, runs, head)
        terms.append(first)
        if second is not None:
            terms.append(second)

    for acceptance in acceptances:
        manual = _chronological(
            [r for r in _runs_for(runs, acceptance) if _str(r, "method") == "manual"]
        )
        if manual:
            signed = bool(_str(manual[-1], "signed_by").strip())
            terms.append(
                Term(
                    f"manual-check-signed:{acceptance['subject']}",
                    signed,
                    "" if signed else "latest manual check-run has no signed_by",
                )
            )

    review_ok = latest_review is not None and _str(latest_review, "result") == "pass"
    terms.append(
        Term(
            "review-at-head",
            review_ok,
            "" if review_ok else f"no passing review check-run at {head or 'unknown head'}",
        )
    )

    worktree = landing_worktree(store, phase_slug, landing)
    if worktree.is_dir():
        terms.append(_descent_term(worktree, head))

    policy = suite.load_suite_policy(store)
    if policy.gate == "required" and policy.mode not in ("none", ""):
        suite_ok = any(
            _is_suite_run(r, phase_slug)
            and _str(r, "result") == "pass"
            and reviewer.revision_matches(_str(r, "revision"), head)
            for r in runs
        )
        terms.append(
            Term(
                "suite-at-head",
                suite_ok,
                "" if suite_ok else f"no passing {suite.suite_subject(phase_slug)} at head",
            )
        )

    blockers = [
        f
        for f in of_type("tuner:finding")
        if _str(f, "effort") == effort
        and _str(f, "needs") == "human"
        and f["lifecycle_state"] not in INACTIVE_FINDING_STATES
    ]
    if blockers:
        for finding in blockers:
            terms.append(
                Term(
                    f"finding-needs-human:{finding['subject']}",
                    False,
                    _str(finding, "claim"),
                )
            )
    else:
        terms.append(Term("no-human-findings", True))
    return terms


def missing_terms(terms: Sequence[Term]) -> list[Term]:
    return [term for term in terms if not term.holds]


def format_missing(terms: Sequence[Term]) -> list[str]:
    return [f"missing {t.name}" + (f": {t.detail}" if t.detail else "") for t in terms]
