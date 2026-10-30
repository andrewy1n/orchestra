"""Oracles for `orchestra status`: one line per effort, and the merged needs-you count with --count."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import helpers as h
from conftest import REPO_ROOT


def _orchestra(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )


def _goal(cli, defs, effort: str) -> None:
    h.create_generic_record(
        cli, defs, "score:effort", subject=effort,
        extra_payload={"goal": f"ship {effort}", "kind": "deliver"},
    )


def _work_item(cli, defs, effort: str, subject: str) -> dict:
    return h.create_generic_record(
        cli, defs, "score:work-item", subject=subject,
        extra_payload={
            "title": f"title of {subject}", "phase": f"{effort}-phase", "kind": "deliver",
            "assignee": "", "effort": effort,
        },
    )


@pytest.fixture()
def seeded(store: Path, cli, resolved_contract) -> Path:
    defs = h.record_defs_by_id(resolved_contract)
    _goal(cli, defs, "busy")
    _goal(cli, defs, "calm")
    running = _work_item(cli, defs, "busy", "busy-running")
    h.transition(cli, "score:work-item", running, "in_progress")
    _work_item(cli, defs, "busy", "busy-ready")
    h.create_generic_record(
        cli, defs, "score:continuity-question", subject="busy",
        extra_payload={"blocking": True, "scope": "busy-scope"},
    )
    return store


def test_r9_status_prints_one_line_per_effort(seeded):
    result = _orchestra("status", str(seeded))
    assert result.returncode == 0, result.stdout + result.stderr
    assert sorted(result.stdout.splitlines()) == [
        "busy: running 1, ready 1, needs-you 1",
        "calm: running 0, ready 0, needs-you 0",
    ]


def test_r10_status_count_prints_the_needs_you_count(seeded):
    result = _orchestra("status", "--count", str(seeded))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "1\n"
