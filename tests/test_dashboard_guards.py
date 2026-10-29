"""The dashboard tolerates a refresh that lands on a screen being built or torn down."""

from __future__ import annotations

import asyncio
import sys

import pytest

pytest.importorskip("textual")

from conftest import REPO_ROOT  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))
from textual.css.query import NoMatches  # noqa: E402
from dashboard import app as app_module  # noqa: E402


class _NeedsScreen(app_module.NeedsYouDetailScreen):
    def __init__(self, present: set[str]) -> None:
        super().__init__(None, "alpha")
        self.present = present
        self.shown = 0

    def query(self, selector=None):
        return [object()] if selector in self.present else []

    async def _show(self, item) -> None:
        self.shown += 1
        raise NoMatches("gone")


class _Pane(app_module.EffortPane):
    def __init__(self, present: set[str]) -> None:
        super().__init__("alpha")
        self.present = present

    def query(self, selector=None):
        return [object()] if selector in self.present else []

    def query_one(self, selector, expect_type=None):
        raise AssertionError(f"painted {selector} on a pane without #goal")


def test_show_ignores_no_matches_when_a_panel_is_missing():
    present = set(app_module.NEEDS_PANELS) - {"#needs-evidence"}
    screen = _NeedsScreen(present)

    asyncio.run(screen.show(None))

    assert screen.shown == 1


def test_show_raises_no_matches_when_every_panel_is_present():
    screen = _NeedsScreen(set(app_module.NEEDS_PANELS))

    with pytest.raises(NoMatches):
        asyncio.run(screen.show(None))


def test_follow_waits_for_the_screen_to_mount():
    screen = _NeedsScreen(set(app_module.NEEDS_PANELS))
    assert screen.ready is False

    asyncio.run(screen.follow(None))

    assert screen.shown == 0


def test_effort_pane_show_returns_when_its_content_is_gone():
    pane = _Pane(set())

    pane.show(None, None, 80, {})

    assert pane.last == (None, None, 80, {})
