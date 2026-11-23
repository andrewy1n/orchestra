from __future__ import annotations

from pathlib import Path

from tests.test_wheel_smoke import (
    _check_ok,
    _created_venvs,
    _events,
    _is_orchestra,
    _outside,
    _require,
    _tokens,
)

_PLUGIN_GROUPS = (
    "orchestra.tuner.verify",
    "orchestra.conductor.land",
    "orchestra.conductor.merge_evidence",
    "orchestra.plugin_api",
)


def _hook_event(events: list[dict], command: str) -> dict:
    def match(event: dict) -> bool:
        tokens = _tokens(event)
        return _is_orchestra(tokens) and command in tokens

    return _require(events, match, f"orchestra {command} did not run")


def _assert_hook(command: str) -> None:
    events = _events()
    event = _hook_event(events, command)
    _check_ok(event, _created_venvs(events))
    assert not (Path(event["cwd"]) / ".git").exists(), event["cwd"]
    assert not event["is_git"], event["cwd"]


def test_wheel_smoke_entry_points_r10_hook_start_runs_without_store():
    _assert_hook("hook-start")


def test_wheel_smoke_entry_points_r10_hook_stop_runs_without_store():
    _assert_hook("hook-stop")


def test_wheel_smoke_entry_points_r10_loads_schema_and_plugin_entry_points():
    events = _events()

    def match(event: dict) -> bool:
        text = event.get("text") or ""
        return "canon.schemas" in text and all(group in text for group in _PLUGIN_GROUPS)

    event = _require(events, match, "no check loaded the entry point groups")
    _check_ok(event, _created_venvs(events))
    assert _outside(Path(event["cwd"])), event["cwd"]
