from __future__ import annotations

import sys

from conftest import REPO_ROOT
from dashboard_progress_support import assessed, phase_row

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.progress import build_progress
from dashboard.backend.stages import surface_progress

FULL_IDS = ["spec", "design", "tasks", "execute", "verify", "land", "close"]


def test_full_phase_surface_lists_all_seven_stages() -> None:
    surface = surface_progress("full", assessed("full"))

    assert [state.stage for state in surface.stages] == FULL_IDS


def test_full_phase_card_shows_all_seven_stages() -> None:
    card = build_progress(phase_row("full", "verifying"), [], [])

    assert [stage.id for stage in card.stages] == FULL_IDS
