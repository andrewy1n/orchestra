"""The shared phase-end text is adapter-neutral; the GitHub landing steps live in their own guide."""

from __future__ import annotations

import re

from helpers import brief_text, land_guide_text, section_text, skill_text

PHASE_END = "\n\n".join(section_text(name) for name in ("phase-end", "land", "phase-close"))
GUIDE = land_guide_text()


def test_shared_phase_end_names_no_github_commands() -> None:
    text = PHASE_END

    assert not re.search(r"\bgh\b", text)
    assert "orchestra close" not in text
    assert "### CI repair loop" not in text
    assert "`MERGED`" not in text


def test_shared_phase_end_names_the_adapter_repair_loop() -> None:
    flat = " ".join(PHASE_END.split())

    assert (
        "When `[land] adapter` is `github-pr`, use the CI repair loop in the repair-ci stage"
        in flat
    )
    assert "`[land] adapter` is `github-pr`" in flat


def test_github_pr_guide_holds_the_ci_repair_loop() -> None:
    text = GUIDE

    assert "# Land with the github-pr adapter" in text
    assert "\n### CI repair loop\n" in text
    assert "`gh run view <run-id> --log-failed`" in text
    assert "`retry_max_fix_tasks`" in text
    assert "`orchestra merge-evidence --phase <phase-slug>`" in text


def test_github_pr_guide_holds_the_close_step() -> None:
    text = GUIDE
    start = text.rfind("\n## Close\n")
    section = " ".join(text[start:].split()) if start != -1 else ""

    assert "`orchestra close --phase <phase-slug>`" in section
    assert "from the main checkout" in section
    assert "asks `gh` for the PR state" in section
    assert "`orchestra close --all`" in section


def test_the_guide_ships_in_the_land_brief() -> None:
    assert section_text("land-github-pr") in brief_text("land")


def test_the_run_skill_points_to_the_guide() -> None:
    text = skill_text("run")

    assert "### CI repair loop" in text
