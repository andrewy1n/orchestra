from __future__ import annotations

from conftest import REPO_ROOT


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_tasks_skill_calls_for_write_scope_planning() -> None:
    text = _flat((REPO_ROOT / "skills/tasks/SKILL.md").read_text())

    assert "Declare known task write scopes and review overlap warnings during planning." in text


def test_planning_mechanics_explains_touch_scope_rules() -> None:
    source = _flat((REPO_ROOT / "shared/planning-mechanics.md").read_text())
    generated = _flat((REPO_ROOT / "skills/tasks/references/planning-mechanics.md").read_text())

    assert source == generated
    assert "repository-relative paths or patterns in `payload.touches`" in source
    assert "`orchestra/score/touches.py`" in source
    assert "`tests/score/test_?.py`" in source
    assert "`skills/**/SKILL.md`" in source
    assert "unknown scope is not empty scope" in source
    assert "treat them as advisory" in source
    assert "Add `depends_on` when tasks must edit the same" in source
