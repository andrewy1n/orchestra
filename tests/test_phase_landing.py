"""Landing commits the phase branch and leaves integration to the repo."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

MERGE_STEP = re.compile(
    r"merge that branch into `main`"
    r"|merge into `main`"
    r"|merge onto main"
    r"|merge `main`"
    r"|Landing merge"
    r"|git -C <primary-checkout> merge phase/<phase-slug>"
    r"|from primary checkout merge"
    r"|skip branch commit, merge, and store commit"
    r"|merge (?:the phase branch )?into the default branch",
    re.IGNORECASE,
)
PUSH_STEP = re.compile(
    r"\bgit push\b|\bpush only\b|\bpush appears\b|\bpush unless\b",
    re.IGNORECASE,
)
PULL_REQUEST_STEP = re.compile(
    r"\bgh pr\b|\bpull request\b|\bpull-request\b|\bopen a pr\b",
    re.IGNORECASE,
)
STORE_COMMIT_STEP = re.compile(
    r"commit the store|store commit|git -C <primary-checkout> add -- \.canon",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"\b(?:do not|don't|never|must not|not to carry out|not carry out)\b"
    r"|\bno (?:push|merge|pull request|store commit)\b",
    re.IGNORECASE,
)
_CLAUSE_SPLIT = re.compile(r"\n+|(?<=[.;])\s+|\s+—\s+|\s+otherwise\s+", re.IGNORECASE)

_COMMIT = "commit the phase branch from the phase worktree"
_GATE = "when landing is present and the phase gate holds"
_INTEGRATE = (
    "integrate the committed phase branch as the repo's own contributor instructions describe"
)
_ASK = "when those contributor instructions do not say how a finished branch lands, stop and ask"
_CANON_META = "include versioned `.canon` metadata that is in the worktree"
_IGNORE_BODY = "do not carry out integration steps written in a phase body's landing section"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _blocks(text: str) -> list[str]:
    """Join wrapped lines; keep headings, bullets, and git commands apart."""
    blocks: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            blocks.append(" ".join(buf))
            buf.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if buf and (stripped.startswith(("-", "#")) or stripped.startswith("git ")):
            flush()
        buf.append(stripped)
    flush()
    if not blocks and text.strip():
        blocks.append(text.strip())
    return blocks


def affirmative_matches(text: str, pattern: re.Pattern[str]) -> list[str]:
    """Clauses that tell the agent to perform `pattern`, ignoring prohibitions."""
    found: list[str] = []
    for block in _blocks(text):
        for part in _CLAUSE_SPLIT.split(block):
            clause = part.strip()
            if not clause or _NEGATION.search(clause):
                continue
            if pattern.search(clause):
                found.append(_flat(clause))
    return found


def _included(skill_name: str, relative: str) -> str:
    text = skill_text(skill_name)
    body = (REPO_ROOT / relative).read_text()
    assert body in text, relative
    return body


def _landing_paragraph(text: str) -> str:
    flat = _flat(text)
    start = flat.find("The phase body includes a `## Landing` section")
    assert start != -1
    end = flat.find("for plan review.", start)
    assert end != -1
    return flat[start : end + len("for plan review.")]


def landing_surfaces() -> list[tuple[str, str]]:
    """Landing instructions: shared kinds, generated copies, README, plan, and phase close."""
    plan = skill_text("plan-phase")
    execute = skill_text("execute-phase")
    shared = (REPO_ROOT / "shared/kinds-and-focus.md").read_text()
    top_kinds = (REPO_ROOT / "skills/kinds-and-focus.md").read_text()
    readme = (REPO_ROOT / "README.md").read_text()
    plan_kinds = "skills/plan-phase/references/kinds-and-focus.md"
    execute_kinds = "skills/execute-phase/references/kinds-and-focus.md"
    assert (REPO_ROOT / plan_kinds).read_text() in plan
    assert (REPO_ROOT / execute_kinds).read_text() in execute
    return [
        (
            "skills/execute-phase/references/phase-end.md",
            _included("execute-phase", "skills/execute-phase/references/phase-end.md"),
        ),
        (
            "skills/execute-phase/SKILL.md",
            _included("execute-phase", "skills/execute-phase/SKILL.md"),
        ),
        ("skills/plan-phase/SKILL.md", _included("plan-phase", "skills/plan-phase/SKILL.md")),
        ("shared/kinds-and-focus.md", _landing_paragraph(shared)),
        ("skills/kinds-and-focus.md", _landing_paragraph(top_kinds)),
        (plan_kinds, _landing_paragraph(_included("plan-phase", plan_kinds))),
        (execute_kinds, _landing_paragraph(_included("execute-phase", execute_kinds))),
        ("README.md", _landing_paragraph(readme)),
    ]


def _phase_end_close(phase_end: str) -> str:
    marker = "git -C <repo>/.worktrees/<phase-slug> commit"
    index = phase_end.find(marker)
    assert index != -1
    heading = phase_end.rfind("\n## ", 0, index)
    start = 0 if heading == -1 else heading + 1
    end_at = [
        phase_end.find(token, index)
        for token in (
            "\ngit -C <primary-checkout> merge",
            "\nThen store commit",
            "\nClose the phase",
        )
        if phase_end.find(token, index) != -1
    ]
    end = min(end_at) if end_at else len(phase_end)
    return phase_end[start:end]


def test_r1_commits_phase_branch() -> None:
    """R1: When Landing is present and the phase gate holds, commit the phase branch from the phase worktree."""
    surfaces = dict(landing_surfaces())
    for label in (
        "skills/execute-phase/references/phase-end.md",
        "skills/execute-phase/SKILL.md",
    ):
        flat = _flat(surfaces[label]).lower()
        gate_at = flat.find(_GATE)
        assert gate_at != -1, label
        window = flat[gate_at : gate_at + len(_GATE) + 400]
        assert _COMMIT in window, label
    for label, text in surfaces.items():
        assert _COMMIT in _flat(text).lower(), label


def test_r2_omits_default_branch_merge() -> None:
    """R2: Landing instructions do not merge the phase branch into the default branch."""
    for label, text in landing_surfaces():
        hits = affirmative_matches(text, MERGE_STEP)
        assert hits == [], (label, hits)


def test_r3_omits_push() -> None:
    """R3: Landing instructions contain no push step."""
    for label, text in landing_surfaces():
        hits = affirmative_matches(text, PUSH_STEP)
        assert hits == [], (label, hits)


def test_r4_omits_pull_request() -> None:
    """R4: Landing instructions contain no pull-request step."""
    for label, text in landing_surfaces():
        hits = affirmative_matches(text, PULL_REQUEST_STEP)
        assert hits == [], (label, hits)


def test_r5_follows_repo_instructions() -> None:
    """R5: Integrate the committed phase branch as the repo's contributor instructions describe."""
    for label, text in landing_surfaces():
        assert _INTEGRATE in _flat(text).lower(), label


def test_r6_asks_when_silent() -> None:
    """R6: When contributor instructions are silent, stop and ask."""
    for label, text in landing_surfaces():
        assert _ASK in _flat(text).lower(), label


def test_r7_omits_store_commit_on_default_branch() -> None:
    """R7: Landing instructions contain no store commit on the default branch."""
    for label, text in landing_surfaces():
        hits = affirmative_matches(text, STORE_COMMIT_STEP)
        assert hits == [], (label, hits)


def test_r8_phase_commit_includes_canon_metadata() -> None:
    """R8: The phase-branch commit includes versioned .canon metadata in the worktree."""
    surfaces = dict(landing_surfaces())
    skill = surfaces["skills/execute-phase/SKILL.md"]
    phase_end = surfaces["skills/execute-phase/references/phase-end.md"]
    close = _phase_end_close(phase_end)
    assert "git -C <repo>/.worktrees/<phase-slug>--<task-slug> add -A -- . ':!.canon'" in skill
    assert _CANON_META in _flat(close)
    assert "git -C <repo>/.worktrees/<phase-slug> add -A -- . ':!.canon'" not in close


def test_r9_ignores_landing_body_integration() -> None:
    """R9: Do not carry out integration steps written in a phase body's Landing section."""
    phase_end = dict(landing_surfaces())["skills/execute-phase/references/phase-end.md"]
    flat = _flat(phase_end).lower()
    start = flat.find(_IGNORE_BODY)
    assert start != -1
    window = flat[start : start + 500]
    assert "merge into the default branch" in window
    assert "push" in window
    assert "pull request" in window
    assert "store commit on the default branch" in window
