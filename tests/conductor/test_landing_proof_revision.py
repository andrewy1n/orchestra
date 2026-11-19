from __future__ import annotations

import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest
from canon_support import create, make_project
from conductor_support import write_policy

from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue, Record
from orchestra.conductor.workflow import (
    WorkflowRunError,
    preview_run,
    run_status,
    start_run,
    step_stage,
)

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


class _Missing:
    pass


_MISSING = _Missing()


def _store_without_validation(
    project: Project, record: Record, field: str, value: JsonValue | _Missing
) -> str:
    store, _ = project._session()
    changed = Record(**record)
    payload = dict(record["payload"])
    if isinstance(value, _Missing):
        del payload[field]
    else:
        payload[field] = value
    changed["payload"] = payload
    store.write_record(changed, expected_revision=record["revision"])
    return record["id"]


def _packet(project: Project, revision: JsonValue | _Missing = HEAD) -> str:
    payload: dict[str, object] = {
        "phase": PHASE,
        "effort": EFFORT,
        "revision": HEAD,
        "base": "main",
        "kind": "claims",
    }
    record = create(project, "conductor:proof-packet", PHASE, payload)
    if revision == HEAD:
        return record["id"]
    return _store_without_validation(project, record, "revision", revision)


def _landing(
    project: Project, head_sha: JsonValue | _Missing = HEAD, result: str = "success"
) -> str:
    payload: dict[str, object] = {
        "phase": PHASE,
        "effort": EFFORT,
        "number": 7,
        "url": "https://github.com/o/r/pull/7",
        "head_sha": HEAD,
        "result": result,
    }
    record = create(project, "conductor:landing", PHASE, payload)
    if head_sha == HEAD:
        return record["id"]
    return _store_without_validation(project, record, "head_sha", head_sha)


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


def test_r9_land_stage_names_the_landing_record_and_field_when_head_sha_is_missing(
    project: Project,
) -> None:
    _packet(project)
    landing_id = _landing(project, _MISSING)

    with pytest.raises(WorkflowRunError, match=rf"{landing_id}.*head_sha"):
        _stage(project)


def test_r9_land_stage_names_the_packet_record_and_field_when_revision_is_missing(
    project: Project,
) -> None:
    packet_id = _packet(project, _MISSING)
    _landing(project)

    with pytest.raises(WorkflowRunError, match=rf"{packet_id}.*revision"):
        _stage(project)


def test_r9_land_stage_does_not_close_when_both_values_are_missing(project: Project) -> None:
    _packet(project, _MISSING)
    _landing(project, _MISSING)

    with pytest.raises(WorkflowRunError, match="head_sha"):
        _stage(project)


def test_r9_land_stage_rejects_a_head_sha_that_is_not_a_string(project: Project) -> None:
    _packet(project)
    landing_id = _landing(project, 123)

    with pytest.raises(WorkflowRunError, match=rf"{landing_id}.*head_sha"):
        _stage(project)


def test_r9_land_step_names_the_landing_record_and_field_when_head_sha_is_missing(
    project: Project,
) -> None:
    _packet(project)
    landing_id = _landing(project, _MISSING)

    with pytest.raises(WorkflowRunError, match=rf"{landing_id}.*head_sha"):
        _land_complete(project)


def test_r9_land_step_names_the_packet_record_and_field_when_revision_is_missing(
    project: Project,
) -> None:
    packet_id = _packet(project, _MISSING)
    _landing(project)

    with pytest.raises(WorkflowRunError, match=rf"{packet_id}.*revision"):
        _land_complete(project)


def test_r9_land_step_does_not_complete_when_both_values_are_missing(project: Project) -> None:
    _packet(project, _MISSING)
    _landing(project, _MISSING)

    with pytest.raises(WorkflowRunError, match="head_sha"):
        _land_complete(project)


def test_r9_a_failed_landing_without_head_sha_is_not_an_error(project: Project) -> None:
    _packet(project)
    _landing(project, _MISSING, result="fail")

    assert _stage(project) == "land"
    assert _land_complete(project) is False
