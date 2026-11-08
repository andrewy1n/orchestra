from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from subprocess import CompletedProcess

import pytest
import test_web_dashboard_launch as launch
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

Cli = Callable[..., CompletedProcess[str]]


def _create(
    cli: Cli,
    record_type: str,
    subject: str,
    payload: dict[str, object],
    sections: tuple[str, ...] = (),
) -> None:
    body = "\n\n".join(f"## {name}\n\nText." for name in sections) or f"text of {subject}\n"
    result = cli(
        "create",
        "--type",
        record_type,
        "--subject",
        subject,
        "--payload",
        json.dumps(payload),
        "--body",
        body,
    )
    assert result.returncode == 0, f"create {record_type} {subject}: {result.stdout}{result.stderr}"


def _transition(cli: Cli, record_type: str, subject: str, state: str) -> None:
    result = cli("update", "--type", record_type, "--subject", subject, "--transition", state)
    assert result.returncode == 0, f"update {record_type} {subject}: {result.stdout}{result.stderr}"


def _phase(cli: Cli, effort: str, subject: str, ordinal: int) -> None:
    _create(
        cli,
        "score:phase",
        subject,
        {"title": subject, "ordinal": ordinal, "effort": effort},
        ("Problem", "Approach", "Exit criteria"),
    )
    _transition(cli, "score:phase", subject, "in_progress")


def _task(cli: Cli, effort: str, phase: str, subject: str, *, running: bool) -> None:
    _create(
        cli,
        "score:work-item",
        subject,
        {
            "title": subject,
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": effort,
            "attempts": 0,
            "estimate_minutes": 0,
        },
        ("Description",),
    )
    if running:
        _transition(cli, "score:work-item", subject, "in_progress")


def _idea(cli: Cli, effort: str, subject: str) -> None:
    _create(
        cli,
        "composer:idea",
        subject,
        {"effort": effort, "status": "open", "source": "chat"},
    )


def _efforts(cli: Cli) -> None:
    for effort in ("alpha", "beta"):
        _create(cli, "score:effort", effort, {"goal": f"ship {effort}", "kind": "deliver"})


def _work_next(store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    port = launch._free_port()
    proc = launch._spawn(
        store, ["--port", str(port)], launch._env(home), tmp_path / "out", tmp_path / "err"
    )
    try:
        status, _content_type, body = launch._get(port, "/api/hub")
        assert status == 200, body
        return json.loads(body)["work_next"]
    finally:
        launch._stop(proc)


def test_r6_running_phase_is_first_over_http_despite_newer_idle_records(
    store: Path, cli: Cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _efforts(cli)
    _phase(cli, "alpha", "running-phase", 1)
    _task(cli, "alpha", "running-phase", "running-task", running=True)
    time.sleep(1.1)
    _phase(cli, "beta", "idle-phase", 1)
    _task(cli, "beta", "idle-phase", "idle-task", running=False)
    _idea(cli, "beta", "newer-idea")

    items = _work_next(store, tmp_path, monkeypatch)

    assert items[0]["subject"] == "running-phase"
    assert items[0]["running"] is True
    assert {item["subject"] for item in items} >= {"idle-phase"}
    assert any(item["title"].startswith("text of newer-idea") for item in items)
    assert all(not item["running"] for item in items[1:])


def test_r7_latest_change_is_first_over_http_when_no_phase_is_running(
    store: Path, cli: Cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _efforts(cli)
    _phase(cli, "alpha", "idle-phase", 1)
    _task(cli, "alpha", "idle-phase", "idle-task", running=False)
    time.sleep(1.1)
    _idea(cli, "beta", "older-idea")
    time.sleep(1.1)
    _idea(cli, "beta", "newest-idea")

    items = _work_next(store, tmp_path, monkeypatch)

    assert not any(item["running"] for item in items)
    assert items[0]["title"].startswith("text of newest-idea")
    order = [item["title"].removeprefix("text of ").strip() or item["subject"] for item in items]
    assert order.index("older-idea") < order.index("idle-phase")
