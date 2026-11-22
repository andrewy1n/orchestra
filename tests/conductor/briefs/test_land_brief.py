from __future__ import annotations

import pytest

from orchestra.conductor.briefs.render import BriefContext, render_brief

REPAIR_LOOP_MARKER = "### CI repair loop"


def _land_brief(adapter: str) -> str:
    ctx = BriefContext(
        step="land",
        phase="demo",
        effort="demo-effort",
        stage=None,
        adapter=adapter,
        weight="full",
    )
    return render_brief(ctx)


def test_github_pr_adapter_brief_contains_repair_loop() -> None:
    assert REPAIR_LOOP_MARKER in _land_brief("github-pr")


@pytest.mark.parametrize("adapter", ["", "other"])
def test_non_github_adapter_brief_omits_repair_loop(adapter: str) -> None:
    text = _land_brief(adapter)

    assert text.strip()
    assert REPAIR_LOOP_MARKER not in text


@pytest.mark.parametrize("adapter", ["github-pr", "", "other"])
def test_adapter_brief_is_non_empty_with_phase_filled(adapter: str) -> None:
    text = _land_brief(adapter)

    assert text.strip()
    assert "demo" in text
    assert "{phase}" not in text
