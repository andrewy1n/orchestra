"""Close is the last phase-end step and runs `orchestra close` after the human merge."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

PHASE_END = REPO_ROOT / "shared/phase-end.md"


def _headings() -> list[str]:
    text = PHASE_END.read_text(encoding="utf-8")
    return re.findall(r"^## (.+)$", text, flags=re.M)


def _close_section() -> str:
    text = PHASE_END.read_text(encoding="utf-8")
    start = text.find("\n## Close\n")
    if start == -1:
        return ""
    return re.sub(r"\s+", " ", text[start:]).strip()


def test_close_is_last_phase_end_step() -> None:
    headings = _headings()

    assert "Close" in headings
    assert headings[-1] == "Close"
    assert headings.index("Land") < headings.index("Close")
    assert "orchestra close --phase <phase-slug>" in _close_section()


def test_close_runs_after_the_human_merge_from_the_main_checkout() -> None:
    section = _close_section()

    assert "after the human merges the PR" in section
    assert "from the main checkout" in section


def test_close_without_landing_keeps_the_manual_phase_close() -> None:
    section = _close_section()

    assert "Without a Landing section" in section
    assert "canon update --type score:phase" in section


def test_the_next_phase_waits_for_close() -> None:
    assert "Plan the next phase only after close" in _close_section()


def test_land_ends_when_ci_passes_and_awaits_the_merge() -> None:
    text = PHASE_END.read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", text)

    assert "Land ends when `orchestra land` exits 0" in flat
    assert "The phase is then awaiting merge" in flat
