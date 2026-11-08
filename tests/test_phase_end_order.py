from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE_END = (ROOT / "skills/verify/references/phase-end.md").read_text(encoding="utf-8")
EXECUTE = (ROOT / "skills/verify/SKILL.md").read_text(encoding="utf-8")


def test_order_line_runs_suite_before_reviewer() -> None:
    flat = " ".join(PHASE_END.split())
    assert flat.index("→ analyze → suite") < flat.index("→ reviewer")


def test_order_suite_section_precedes_reviewer_section() -> None:
    assert PHASE_END.index("\n## Suite\n") < PHASE_END.index("\n## Reviewer\n")


def test_order_verify_steps_lists_suite_before_reviewer() -> None:
    flat = " ".join(EXECUTE.split())
    assert flat.index("orchestra analyze") < flat.index("orchestra suite policy")
    assert flat.index("orchestra suite policy") < flat.index("phase reviewer")
    assert flat.index("phase reviewer") < flat.index("integration report")


def test_order_failing_required_suite_creates_fix_tasks_before_reviewer() -> None:
    flat = " ".join(PHASE_END.split())
    assert "Create the fix work-items before the reviewer starts" in flat


def test_order_review_brief_command_passes_the_phase() -> None:
    assert "orchestra review-brief --phase <phase-slug>" in PHASE_END
