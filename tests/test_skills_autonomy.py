from __future__ import annotations

from helpers import skill_text


def _flat(name: str) -> str:
    return " ".join(skill_text(name).split())


def test_r02_plan_phase_skips_the_gate_at_auto_plan_and_auto_phases() -> None:
    text = _flat("tasks")
    assert "If the effort's `autonomy` is `auto-plan` or `auto-phases`, skip the gate" in text
    assert "Otherwise (`gated` or missing) create a blocking `score:continuity-question`" in text


def test_r03_execute_phase_plans_the_next_phase_without_asking_at_auto_phases() -> None:
    text = _flat("execute")
    assert "At `auto-phases`, plan and promote the next phase without asking" in text
    assert "`gated` and `auto-plan`, ask first" in text


def test_r04_execute_phase_stops_at_every_level_for_failures_findings_pushes_and_merges() -> None:
    text = _flat("execute")
    assert "At every level, stop for a failed check, a needs-human finding, a push, or a merge" in text


def test_r06_the_light_phase_gate_reads_the_effort_autonomy() -> None:
    text = _flat("tasks")
    assert "Skip this gate at `auto-plan` and `auto-phases`" in text
    assert "effort-autonomy lands" not in text
