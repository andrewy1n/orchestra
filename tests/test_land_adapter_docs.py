"""The shared phase-end text is adapter-neutral; the GitHub landing steps live in their own guide."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT

PHASE_END = REPO_ROOT / "shared/phase-end.md"
GUIDE = REPO_ROOT / "shared/land-github-pr.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def test_shared_phase_end_names_no_github_commands() -> None:
    text = _text(PHASE_END)

    assert not re.search(r"\bgh\b", text)
    assert "orchestra close" not in text
    assert "### CI repair loop" not in text
    assert "`MERGED`" not in text


def test_shared_phase_end_points_to_the_adapter_guide() -> None:
    flat = " ".join(_text(PHASE_END).split())

    assert "`land-github-pr.md`" in flat
    assert "`[land] adapter` is `github-pr`" in flat


def test_github_pr_guide_holds_the_ci_repair_loop() -> None:
    text = _text(GUIDE)

    assert "# Land with the github-pr adapter" in text
    assert "\n### CI repair loop\n" in text
    assert "`gh run view <run-id> --log-failed`" in text
    assert "`retry_max_fix_tasks`" in text


def test_github_pr_guide_holds_the_close_step() -> None:
    text = _text(GUIDE)
    start = text.find("\n## Close\n")
    section = " ".join(text[start:].split()) if start != -1 else ""

    assert "`orchestra close --phase <phase-slug>`" in section
    assert "from the main checkout" in section
    assert "asks `gh` for the PR state" in section
    assert "`orchestra close --all`" in section


def test_the_guide_ships_to_the_verify_and_run_skills() -> None:
    for skill in ("verify", "run"):
        copy = REPO_ROOT / "skills" / skill / "references" / "land-github-pr.md"
        assert copy.exists(), skill
        assert copy.read_text(encoding="utf-8") == _text(GUIDE)


def test_the_run_skill_points_to_the_guide() -> None:
    text = (REPO_ROOT / "skills/run/SKILL.md").read_text(encoding="utf-8")

    assert "land-github-pr.md" in text
