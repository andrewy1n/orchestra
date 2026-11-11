from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGAGE = (ROOT / "skills" / "engage" / "SKILL.md").read_text(encoding="utf-8")


def test_engage_names_the_repair_link_record() -> None:
    assert "conductor:repair-link" in ENGAGE


def test_engage_names_the_phase_field_of_the_repair_link() -> None:
    assert "`phase`" in ENGAGE
    assert "conductor:repair-link" in ENGAGE


@pytest.mark.parametrize(
    "cause", ["spec-gap", "verification-miss", "requirement-change", "no-phase"]
)
def test_engage_names_each_repair_link_cause(cause: str) -> None:
    assert f"`{cause}`" in ENGAGE
