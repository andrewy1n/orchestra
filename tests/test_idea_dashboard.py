"""Oracle tests for composer:idea in the dashboard backlog panel."""

from __future__ import annotations

import json
import sys

import pytest

pytest.importorskip("textual")

import helpers as h
from conftest import REPO_ROOT, stamped_store

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard import model  # noqa: E402
from dashboard import app as app_module  # noqa: E402
from test_dashboard_app import (  # noqa: E402
    _dashboard_ready,
    _detail_run,
    _focus_backlog,
    _phase,
    _until,
    _wait_workers,
)
from test_dashboard_model import _effort, _goal, _target  # noqa: E402


@pytest.fixture()
def defs(resolved_contract):
    return h.record_defs_by_id(resolved_contract)


def _idea(cli, defs, subject: str, effort: str, *, status: str = "open", source: str = "",
          phase: str = "", body: str = "") -> dict:
    payload = {"effort": effort, "status": status}
    if source:
        payload["source"] = source
    if phase:
        payload["phase"] = phase
    args = [
        "create", "--type", "composer:idea", "--subject", subject,
        "--payload", json.dumps(payload),
    ]
    if body:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def _current_idea(cli, subject: str) -> dict:
    result = cli(
        "list", "--type", "composer:idea", "--subject", subject,
        "--exact-subject", "--full",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    records = json.loads(result.stdout)["records"]
    assert len(records) == 1, records
    return records[0]


def _seed_idea_backlog(cli, defs):
    h.create_generic_record(
        cli, defs, "score:effort", subject="alpha",
        extra_payload={"goal": "ship backlog panel", "kind": "deliver"},
    )
    _phase(cli, defs, "alpha", "b-phase", 1, "in_progress")
    promote = _idea(
        cli, defs, "park-promote", "alpha",
        body="## Note\n\npromote me",
    )
    dismiss = _idea(
        cli, defs, "park-dismiss", "alpha",
        body="## Note\n\ndismiss me",
    )
    closed = _idea(cli, defs, "park-closed", "alpha")
    cli(
        "supersede", "--type", "composer:idea", "--id", closed["id"],
        "--expected-revision", "@current",
        "--payload", json.dumps({"effort": "alpha", "status": "dismissed"}),
    )
    return promote, dismiss


def test_r9_dashboard_backlog_panel_lists_open_ideas_grouped_by_effort(store, cli, defs):
    _goal(cli, defs, "alpha")
    _goal(cli, defs, "beta")
    open_a = _idea(cli, defs, "park-a", "alpha", body="## Note\n\ndo alpha later")
    _idea(cli, defs, "park-b", "beta", body="## Note\n\ndo beta later")
    promoted = _idea(cli, defs, "park-promoted", "alpha")
    cli(
        "supersede", "--type", "composer:idea", "--id", promoted["id"],
        "--expected-revision", "@current",
        "--payload", json.dumps({"effort": "alpha", "status": "promoted"}),
    )
    dismissed = _idea(cli, defs, "park-dismissed", "alpha")
    cli(
        "supersede", "--type", "composer:idea", "--id", dismissed["id"],
        "--expected-revision", "@current",
        "--payload", json.dumps({"effort": "alpha", "status": "dismissed"}),
    )

    snapshot = model.load_snapshot(_target(store))
    alpha = _effort(snapshot, "alpha")
    beta = _effort(snapshot, "beta")
    assert [item.subject for item in alpha.backlog] == ["park-a"]
    assert alpha.backlog[0].id == open_a["id"]
    assert alpha.backlog[0].text == "do alpha later"
    assert alpha.backlog[0].record_type == "composer:idea"
    assert [item.subject for item in beta.backlog] == ["park-b"]
    assert all(item.status == "open" for item in alpha.backlog + beta.backlog)


def test_r10_dashboard_promote_supersedes_open_idea_to_promoted(store, cli, defs, monkeypatch):
    stamped_store(store, "idea-promote-r10", lambda root, c, d: _seed_idea_backlog(c, d))
    monkeypatch.setattr(app_module.DashboardApp, "copy_to_clipboard", lambda self, text: None)

    async def scenario(app, pilot):
        await _until(pilot, lambda: _dashboard_ready(app))
        await _wait_workers(app)
        await pilot.pause()
        snapshot = model.load_snapshot(app.target)
        open_ideas = [
            item
            for view in snapshot.efforts
            for item in view.backlog
            if item.record_type == "composer:idea"
        ]
        assert len(open_ideas) == 2
        await _until(pilot, lambda: app.query_one("#backlog").option_count == 2)
        item = await _focus_backlog(app, pilot, "park-promote")
        assert item.record_type == "composer:idea"
        await pilot.press("p")
        await _wait_workers(app)
        await pilot.pause()
        current = _current_idea(cli, "park-promote")
        assert current["payload"]["status"] == "promoted"

    _detail_run(store, (120, 40), scenario)


def test_r11_dashboard_dismiss_supersedes_open_idea_to_dismissed(store, cli, defs):
    stamped_store(store, "idea-dismiss-r11", lambda root, c, d: _seed_idea_backlog(c, d))

    async def scenario(app, pilot):
        await _until(pilot, lambda: _dashboard_ready(app))
        await _wait_workers(app)
        await pilot.pause()
        snapshot = model.load_snapshot(app.target)
        open_ideas = [
            item
            for view in snapshot.efforts
            for item in view.backlog
            if item.record_type == "composer:idea"
        ]
        assert len(open_ideas) == 2
        await _until(pilot, lambda: app.query_one("#backlog").option_count == 2)
        await _focus_backlog(app, pilot, "park-dismiss")
        await pilot.press("d")
        await _wait_workers(app)
        await pilot.pause()
        current = _current_idea(cli, "park-dismiss")
        assert current["payload"]["status"] == "dismissed"

    _detail_run(store, (120, 40), scenario)
