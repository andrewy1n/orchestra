from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import create, make_project

from dashboard.backend.snapshot import load_snapshot
from orchestra import views
from orchestra.canon.types import Record
from orchestra.conductor import autonomy

_IDS = itertools.count()


def _constraint(subject: str, effort: str) -> Record:
    n = next(_IDS)
    return {
        "id": f"c{n}",
        "record_type": "score:constraint",
        "subject": subject,
        "payload": {"statement": "", "applies_to": "", "effort": effort},
        "lifecycle_state": "active",
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": "2026-11-01T00:00:00+00:00",
    }


@pytest.mark.parametrize(
    "statement",
    [
        "Do not promote the next phase without asking.",
        "Plan-review gates are not preauthorized.",
        "Never plan and promote each next phase without asking; ask first.",
        "Plan-review gates are preauthorized for the login phase only.",
        "Plan-review gates are preauthorized for phase x only.",
        "Retired: replaced by the effort field autonomy=auto-plan on alpha.",
    ],
)
def test_r07_review_fix_a_restricting_or_scoped_statement_grants_nothing(statement: str) -> None:
    assert autonomy.classify(statement) is None


@pytest.mark.parametrize(
    ("statement", "level"),
    [
        (
            "Plan-review gates for every record-diet phase are preauthorized by the user; plan "
            "and execute each phase without asking. Stop for failures, needs-human findings, "
            "pushes, and merges; merges still need user approval.",
            "auto-plan",
        ),
        (
            "Plan and promote each next phase without asking once the current one closes; stop "
            "only for failures, needs-human findings, or a push or merge",
            "auto-phases",
        ),
    ],
)
def test_r07_review_fix_the_real_grants_still_map(statement: str, level: str) -> None:
    assert autonomy.classify(statement) == level


def test_r07_review_fix_the_effort_comes_from_applies_to_or_the_subject_suffix() -> None:
    known = {"alpha", "dashboard-features", "features"}
    plain = _constraint("anything", "missing")
    plain["payload"]["applies_to"] = "alpha"
    assert autonomy.resolve_effort(plain, known) == "alpha"
    suffixed = _constraint("dashboard-autonomy-dashboard-features", "missing")
    assert autonomy.resolve_effort(suffixed, known) == "dashboard-features"
    assert autonomy.resolve_effort(_constraint("unrelated", "missing"), known) == ""


def test_r08_review_fix_apply_never_lowers_a_level(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(
        project,
        "score:effort",
        "alpha",
        {"goal": "g", "kind": "deliver", "autonomy": "auto-phases"},
    )
    create(
        project,
        "score:constraint",
        "alpha-gates",
        {
            "statement": "Plan-review gates are preauthorized by the user.",
            "applies_to": "alpha",
            "effort": "alpha",
        },
    )
    mappings, skipped = autonomy.plan_migration(project)
    assert skipped == []
    assert autonomy.apply_migration(project, mappings) == {"alpha": "auto-plan"}
    assert project.resolve("score:effort", "alpha")["payload"]["autonomy"] == "auto-phases"
    retired = project.resolve("score:constraint", "alpha-gates")["payload"]["statement"]
    assert str(retired).startswith("Retired:")


def test_r12_review_fix_the_clock_treats_a_naive_timestamp_as_utc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ORCHESTRA_NOW", "2026-11-20T12:00:00")
    assert views.clock() == datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)


def test_r12_review_fix_snapshot_dormancy_matches_the_handoff_rule(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    for effort in ("busy", "quiet"):
        create(project, "score:effort", effort, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:constraint",
        "busy-rule",
        {"statement": "Keep it small.", "applies_to": "all", "effort": "busy"},
    )
    later = datetime.now(timezone.utc) + timedelta(days=10)
    expected = set(views.dormant_efforts(project.records(), later))
    snapshot = load_snapshot(project, now=later)
    assert {v.effort for v in snapshot.efforts if v.dormant} == expected == {"busy", "quiet"}
