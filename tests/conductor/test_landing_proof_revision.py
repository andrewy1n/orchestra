from __future__ import annotations

import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest
from canon_support import create, make_project
from conductor_support import write_policy

from orchestra.canon.project import Project
from orchestra.conductor.workflow import preview_run, run_status, start_run, step_stage

EFFORT = "e1"
PHASE = "p1"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OTHER = "b" * 40
LANDING_BODY = (
    "## Problem\nMeet the contract.\n"
    "## Requirements\nR1: Preserve workflow behavior.\n"
    "## Approach\nUse the reviewed design.\n"
    "## Exit criteria\nVerify the result.\n"
    "## Landing\nBranch phase/p1.\n"
)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    ticks: Iterator[int] = itertools.count()
    monkeypatch.setattr(
        "orchestra.canon.record.now", lambda: f"2026-11-01T00:00:{next(ticks):02d}+00:00"
    )
    store = make_project(tmp_path)
    write_policy(store.project_root)
    create(store, "score:effort", EFFORT, {"goal": "Land", "kind": "deliver"})
    create(
        store,
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT, "weight": "light"},
        LANDING_BODY,
    )
    return store


def _packet(project: Project, revision: str) -> None:
    payload: dict[str, object] = {
        "phase": PHASE,
        "effort": EFFORT,
        "revision": revision,
        "base": "main",
        "kind": "claims",
    }
    create(project, "conductor:proof-packet", PHASE, payload)


def _landing(project: Project, head_sha: str, result: str = "success") -> None:
    create(
        project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": head_sha,
            "result": result,
        },
    )


def _land_complete(project: Project) -> bool:
    run = start_run(project, preview_run(project, EFFORT, PHASE, "single-step", step="land"))
    return run_status(project, run["subject"]).complete


def _stage(project: Project) -> str | None:
    return step_stage(project, project.records(), PHASE, "land")


def test_r1_land_completes_when_the_landing_head_equals_the_packet_revision_in_another_case(
    project: Project,
) -> None:
    _packet(project, HEAD.upper())
    _landing(project, HEAD)

    assert _land_complete(project) is True


def test_r1_land_completes_at_the_latest_packet_when_an_older_packet_differs(
    project: Project,
) -> None:
    _packet(project, OTHER)
    _packet(project, HEAD)
    _landing(project, HEAD)

    assert _land_complete(project) is True


def test_r2_stage_is_close_when_the_landing_head_equals_the_packet_revision_in_another_case(
    project: Project,
) -> None:
    _packet(project, HEAD.upper())
    _landing(project, HEAD)

    assert _stage(project) == "close"


def test_r2_stage_is_close_at_the_latest_packet_when_an_older_packet_differs(
    project: Project,
) -> None:
    _packet(project, OTHER)
    _packet(project, HEAD)
    _landing(project, HEAD)

    assert _stage(project) == "close"


def test_r3_full_landing_head_matches_a_seven_character_packet_revision(
    project: Project,
) -> None:
    _packet(project, HEAD[:7])
    _landing(project, HEAD)

    assert _land_complete(project) is True
    assert _stage(project) == "close"


def test_r3_full_landing_head_does_not_match_a_six_character_packet_revision(
    project: Project,
) -> None:
    _packet(project, HEAD[:6])
    _landing(project, HEAD)

    assert _land_complete(project) is False
    assert _stage(project) == "land"


def test_r4_land_stays_incomplete_when_the_landing_head_differs_from_the_packet_revision(
    project: Project,
) -> None:
    _packet(project, HEAD)
    _landing(project, OTHER)

    assert _land_complete(project) is False


def test_r5_land_stays_incomplete_when_a_newer_packet_differs_from_the_landing_head(
    project: Project,
) -> None:
    _packet(project, HEAD)
    _packet(project, OTHER)
    _landing(project, HEAD)

    assert _land_complete(project) is False


def test_r5_land_stays_incomplete_when_a_newer_abbreviated_packet_differs_from_the_landing_head(
    project: Project,
) -> None:
    _packet(project, HEAD[:7])
    _packet(project, OTHER[:7])
    _landing(project, HEAD)

    assert _land_complete(project) is False


def test_r6_stage_is_land_when_the_landing_head_differs_from_the_packet_revision(
    project: Project,
) -> None:
    _packet(project, HEAD)
    _landing(project, OTHER)

    assert _stage(project) == "land"


def test_r6_stage_is_land_when_a_newer_packet_differs_from_the_landing_head(
    project: Project,
) -> None:
    _packet(project, HEAD)
    _packet(project, OTHER)
    _landing(project, HEAD)

    assert _stage(project) == "land"


def test_r6_stage_is_land_when_the_successful_landing_has_no_belonging_packet(
    project: Project,
) -> None:
    _landing(project, HEAD)

    assert _stage(project) == "land"
    assert _land_complete(project) is False
