"""Oracle tests for composer:idea in the dashboard backlog panel."""

from __future__ import annotations

import json
import sys

import pytest

import helpers as h
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend import model  # noqa: E402
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
