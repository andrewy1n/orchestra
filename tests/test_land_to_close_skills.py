"""Verify ends at the gate and the proof packet. Land is its own phase-end step."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT

VERIFY = REPO_ROOT / "skills/verify/SKILL.md"
PHASE_END = REPO_ROOT / "shared/phase-end.md"


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).strip()


def _land_section() -> str:
    text = PHASE_END.read_text(encoding="utf-8")
    start = text.find("\n## Land\n")
    if start == -1:
        return ""
    following = re.search(r"\n## (?!Land\n)", text[start + 1 :])
    end = start + 1 + following.start() if following else len(text)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def test_verify_ends_at_gate() -> None:
    flat = _flat(VERIFY)

    assert "With a Landing section, verify ends here" in flat
    assert "Run `orchestra gate`" in flat
    assert flat.index("Run `orchestra gate`") < flat.index("verify ends here")


def test_verify_writes_proof_packet() -> None:
    flat = _flat(VERIFY)

    assert "write the proof packet at the phase head" in flat
    assert "verify ends here" in flat
    assert flat.index("write the proof packet at the phase head") < flat.index("verify ends here")


def test_verify_does_not_run_land() -> None:
    text = VERIFY.read_text(encoding="utf-8")

    assert "Verify does not commit, push, or run land" in _flat(VERIFY)
    assert "orchestra land" not in text


def test_land_is_separate_phase_end_step() -> None:
    phase_end = PHASE_END.read_text(encoding="utf-8")

    assert "\n## Land\n" in phase_end
    assert "## Commit the phase branch and stop" not in phase_end
    assert phase_end.find("\n## Proof packet\n") < phase_end.find("\n## Land\n")
    assert "Land section" in _flat(VERIFY)


def test_land_requires_landing_section() -> None:
    assert "Land runs only when the phase has a Landing section" in _land_section()


def test_land_requires_gate() -> None:
    section = _land_section()

    assert "Land runs only when the gate holds at the phase head" in section
    assert "proof packet exists at that head" in section


def test_land_commits_phase_branch() -> None:
    section = (
        _land_section()
        .lower()
        .replace("`orchestra land --phase <phase-slug>`", "orchestra land --phase <phase-slug>")
    )

    commit = "commit the phase branch from the phase worktree"
    assert commit in section
    assert "orchestra land --phase <phase-slug>" in section
    assert section.index(commit) < section.index("orchestra land --phase <phase-slug>")
