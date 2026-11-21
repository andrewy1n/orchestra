"""Component-owned verbs refuse a directory with no store as `store_not_ready`."""

from __future__ import annotations

from pathlib import Path

import pytest
from interfaces_support import invoke

NO_STORE = "No artifact store for"
REFUSAL_CODE = 2
MINIMAL_CONFIG = (
    '[verify.stages]\ntask = ["unit"]\nphase = ["unit"]\nmilestone = ["unit"]\n\n'
    '[verify.unit]\nrunner = ["true", "{tests}", "{report}"]\n'
)

CONDUCTOR_SUITE_GATE = [
    ("gate", "p1"),
    ("analyze", "p1"),
    ("review-brief", "--phase", "p1"),
]

CONDUCTOR_WAVE_TASK = [
    ("wave", "start", "p1"),
    ("wave", "end", "p1"),
    ("wave", "resolve", "p1", "a"),
    ("task", "land", "--evidence", "x", "t"),
]

GROUPS = {
    "conductor_suite_gate": CONDUCTOR_SUITE_GATE,
    "conductor_wave_task": CONDUCTOR_WAVE_TASK,
}

CASES = [
    pytest.param(argv, id=f"{group}-{'_'.join(argv).replace('-', '_')}")
    for group, commands in GROUPS.items()
    for argv in commands
]


@pytest.mark.parametrize("argv", CASES)
def test_no_store_is_store_not_ready_with_searched_paths(
    argv: tuple[str, ...], bare_dir: Path
) -> None:
    (bare_dir / "orchestra.toml").write_text(MINIMAL_CONFIG, encoding="utf-8")
    result = invoke("orchestra", list(argv), bare_dir)
    text = result.out + result.err
    assert result.code == REFUSAL_CODE, text
    assert NO_STORE in text
    assert "store_not_ready" in text
    assert "searched" in text
    assert str(bare_dir) in text
