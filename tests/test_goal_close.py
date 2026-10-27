"""Closing an effort supersedes its goal and position with status closed; views drop it."""

from __future__ import annotations

import json

from orchestra.canon.project import open_store

import helpers as h
from orchestra import views


def _effort(cli, defs, effort: str) -> tuple[dict, dict]:
    goal = h.create_generic_record(
        cli, defs, "score:effort", subject=effort,
        extra_payload={"goal": f"goal of {effort}", "kind": "deliver"},
    )
    phase = h.create_generic_record(
        cli, defs, "score:phase", subject=f"{effort}-phase",
        extra_payload={"title": "only phase", "ordinal": 1, "effort": effort},
    )
    position = h.create_generic_record(
        cli, defs, "score:position", subject=effort,
        extra_payload={"position": f"position of {effort}", "scope": "effort", "effort": effort, "phase": phase["subject"]},
    )
    return goal, position


def _close(cli, record_type: str, record: dict) -> None:
    payload = {**record["payload"], "status": "closed"}
    result = cli(
        "supersede", "--type", record_type, "--id", record["id"],
        "--expected-revision", record["revision"], "--payload", json.dumps(payload),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _render(cli, *args: str) -> str:
    result = cli(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def _handoff(store) -> str:
    return views.render_view(views.VIEWS["handoff"], views.load_records(open_store(store)))


def test_closed_effort_leaves_the_handoff(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    _effort(cli, defs, "open-effort")
    goal, position = _effort(cli, defs, "done-effort")
    _close(cli, "score:effort", goal)
    _close(cli, "score:position", position)

    handoff = _handoff(store)
    assert "done-effort" not in handoff
    assert "goal of open-effort" in handoff and "position of open-effort" in handoff
    assert _render(cli, "validate")


def test_reopened_effort_returns_to_the_handoff(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    goal, position = _effort(cli, defs, "back-effort")
    _close(cli, "score:effort", goal)
    _close(cli, "score:position", position)
    for record_type, subject in (("score:effort", "back-effort"), ("score:position", "back-effort")):
        closed = json.loads(_render(cli, "list", "--type", record_type, "--subject", subject, "--state", "active", "--full"))["records"][0]
        result = cli(
            "supersede", "--type", record_type, "--id", closed["id"], "--expected-revision", closed["revision"],
            "--payload", json.dumps({"status": "open"}),
        )
        assert result.returncode == 0, result.stdout + result.stderr

    assert "back-effort" in _handoff(store)
    assert _render(cli, "validate")


def test_status_rejects_values_other_than_open_or_closed(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    goal, _ = _effort(cli, defs, "some-effort")
    payload = {**goal["payload"], "status": "finished"}
    result = cli(
        "supersede", "--type", "score:effort", "--id", goal["id"],
        "--expected-revision", goal["revision"], "--payload", json.dumps(payload),
    )
    assert result.returncode != 0
