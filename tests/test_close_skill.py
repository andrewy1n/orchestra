"""Close is the last phase-end step and runs `orchestra close` after the human merge."""

from __future__ import annotations

import re

from helpers import land_guide_text

PHASE_END = land_guide_text()
GUIDE = land_guide_text()


def _headings() -> list[str]:
    text = PHASE_END
    return re.findall(r"^## (.+)$", text, flags=re.M)


def _close_section() -> str:
    text = PHASE_END
    start = text.find("\n## Close\n")
    if start == -1:
        return ""
    end = text.find("\n## Close\n", start + 1)
    return re.sub(r"\s+", " ", text[start : end if end != -1 else None]).strip()


def _guide_close_section() -> str:
    text = GUIDE
    start = text.rfind("\n## Close\n")
    return re.sub(r"\s+", " ", text[start:]).strip() if start != -1 else ""


def test_close_is_last_phase_end_step() -> None:
    headings = _headings()

    assert "Close" in headings
    assert headings[-1] == "Close"
    assert headings.index("Land") < headings.index("Close")
    assert "orchestra close --phase <phase-slug>" in _guide_close_section()


def test_close_runs_after_the_human_merge_from_the_main_checkout() -> None:
    section = _guide_close_section()

    assert "after the human merges the PR" in section
    assert "from the main checkout" in section


def test_close_without_landing_keeps_the_manual_phase_close() -> None:
    section = _close_section()

    assert "Without a Landing section" in section
    assert "canon update --type score:phase" in section


def test_the_next_phase_waits_for_close() -> None:
    assert "Plan the next phase only after close" in _close_section()
    assert "Plan the next phase only after close" in _guide_close_section()


def test_land_ends_when_ci_passes_and_awaits_the_merge() -> None:
    flat = re.sub(r"\s+", " ", PHASE_END)

    assert "Land ends when `orchestra land` exits 0" in flat
    assert "waits for the human merge" in flat
    assert "awaiting merge" in re.sub(r"\s+", " ", GUIDE)


def test_close_defers_the_adapter_steps_to_the_adapter_brief() -> None:
    section = _close_section()

    assert "use the adapter's close instructions in this brief" in section
    assert "orchestra close" not in section
