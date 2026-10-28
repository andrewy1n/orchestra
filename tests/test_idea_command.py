"""Oracle tests for the orchestra idea command (idea-triage phase)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

ORCHESTRA_CMD = [sys.executable, "-m", "orchestra.cli"]


def _orchestra_env() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(REPO_ROOT)]
    existing = env.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    return env


def run_orchestra(store: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*ORCHESTRA_CMD, *args],
        capture_output=True,
        text=True,
        cwd=str(store),
        env=_orchestra_env(),
    )


def _list_ideas(cli, *, subject: str | None = None) -> list[dict]:
    args = ["list", "--type", "composer:idea", "--state", "active", "--full"]
    if subject is not None:
        args.extend(["--subject", subject, "--exact-subject"])
    result = cli(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["records"]


def _create_area(cli, subject: str) -> dict:
    result = cli(
        "create",
        "--type",
        "composer:area",
        "--subject",
        subject,
        "--payload",
        json.dumps({"title": f"Area {subject}"}),
        "--body",
        "## Scope\n\nScope for testing.",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def test_r1_idea_command_creates_open_idea_with_slugified_subject(store, cli):
    title = "Capture Me"
    expected_subject = "capture-me"
    result = run_orchestra(store, "idea", title)
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject=expected_subject)
    assert len(ideas) == 1, ideas
    assert ideas[0]["subject"] == expected_subject
    assert ideas[0]["payload"]["status"] == "open"


def test_r3_idea_command_sets_area_flag(store, cli):
    _create_area(cli, "dashboard")
    result = run_orchestra(store, "idea", "Area Tagged", "--area", "dashboard")
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject="area-tagged")
    assert len(ideas) == 1, ideas
    assert ideas[0]["payload"].get("area") == "dashboard"


def test_r7_idea_command_refuses_duplicate_subject(store, cli):
    title = "Duplicate Title"
    subject = "duplicate-title"
    first = run_orchestra(store, "idea", title)
    assert first.returncode == 0, first.stdout + first.stderr
    assert _list_ideas(cli, subject=subject)
    before = _list_ideas(cli)
    result = run_orchestra(store, "idea", title)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "invalid choice: 'idea'" not in result.stderr
    after = _list_ideas(cli)
    assert after == before


def test_r8_idea_command_refuses_unknown_area(store, cli):
    before = _list_ideas(cli)
    result = run_orchestra(store, "idea", "Nowhere", "--area", "missing-area")
    assert result.returncode != 0, result.stdout + result.stderr
    assert "invalid choice: 'idea'" not in result.stderr
    after = _list_ideas(cli)
    assert after == before
