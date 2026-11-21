from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from canon_support import create, make_project

from dashboard.backend import store
from dashboard.backend.hub import build_hub
from dashboard.backend.snapshot import load_snapshot, load_work_snapshot
from orchestra.conductor.effort_status import effort_statuses

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


def _world(tmp_path: Path):
    project = make_project(tmp_path)
    for effort in ("busy", "quiet", "done"):
        create(project, "score:effort", effort, {"goal": f"goal of {effort}", "kind": "deliver"})
    create(
        project,
        "score:phase",
        "next-up",
        {"title": "Next", "ordinal": 1, "effort": "busy"},
        PHASE_BODY,
    )
    shipped = create(
        project,
        "score:phase",
        "shipped",
        {"title": "Shipped", "ordinal": 1, "effort": "done"},
        PHASE_BODY,
    )
    for state in ("in_progress", "done"):
        shipped = project.update(shipped["id"], transition=state)
    return project, datetime.now(timezone.utc) + timedelta(days=10)


def test_dashboard_status_matches_the_shared_operation_and_hides_finished(
    tmp_path: Path,
) -> None:
    project, later = _world(tmp_path)
    expected = effort_statuses(store.catalog_records(project), later)
    assert set(expected.values()) == {"live", "dormant", "finished"}

    snapshot = load_snapshot(project, now=later)
    shown = {view.effort: getattr(view, "status", None) for view in snapshot.efforts}
    assert shown == expected

    work = load_work_snapshot(project, now=later)
    assert {view.effort for view in work.efforts} == {
        name for name, status in expected.items() if status == "live"
    }

    hub = build_hub(snapshot, later)
    assert {item.effort for item in hub.active_phases} <= {
        name for name, status in expected.items() if status == "live"
    }
