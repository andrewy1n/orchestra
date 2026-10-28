"""Oracle tests for orchestra view roadmap (idea-triage phase)."""

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


def roadmap(store: Path) -> str:
    result = run_orchestra(store, "view", "roadmap")
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


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


def _create_effort(cli, subject: str) -> dict:
    result = cli(
        "create",
        "--type",
        "score:effort",
        "--subject",
        subject,
        "--payload",
        json.dumps({"goal": f"Goal {subject}", "kind": "deliver"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def _create_idea(
    cli,
    subject: str,
    *,
    status: str = "open",
    area: str | None = None,
    effort: str | None = None,
) -> dict:
    payload: dict[str, str] = {"status": status}
    if area is not None:
        payload["area"] = area
    if effort is not None:
        payload["effort"] = effort
    result = cli(
        "create",
        "--type",
        "composer:idea",
        "--subject",
        subject,
        "--payload",
        json.dumps(payload),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.find(marker)
    assert start != -1, f"missing section {heading!r} in:\n{text}"
    rest = text[start + len(marker) :]
    next_heading = rest.find("\n## ")
    if next_heading == -1:
        return rest
    return rest[:next_heading]


def test_r10_roadmap_groups_open_and_promoted_ideas_by_area(store, cli):
    _create_area(cli, "dashboard")
    _create_area(cli, "cli")
    _create_idea(cli, "dash-open", area="dashboard", status="open")
    _create_idea(cli, "cli-promoted", area="cli", status="promoted")
    text = roadmap(store)
    dash = _section(text, "dashboard")
    cli_block = _section(text, "cli")
    assert "**dash-open**" in dash
    assert "**cli-promoted**" in cli_block
    assert "**cli-promoted**" not in dash
    assert "**dash-open**" not in cli_block


def test_r11_roadmap_lists_untriaged_ideas_under_untriaged(store, cli):
    _create_idea(cli, "no-area-yet", status="open")
    text = roadmap(store)
    untriaged = _section(text, "untriaged")
    assert "**no-area-yet**" in untriaged


def test_r12_roadmap_hides_dismissed_ideas(store, cli):
    _create_idea(cli, "still-open", status="open")
    _create_idea(cli, "gone-away", status="dismissed")
    text = roadmap(store)
    assert "**still-open**" in text
    assert "gone-away" not in text


def test_r13_roadmap_shows_effort_for_promoted_ideas(store, cli):
    _create_effort(cli, "composer")
    _create_idea(cli, "shipped", status="promoted", effort="composer")
    text = roadmap(store)
    line = next(line for line in text.splitlines() if "**shipped**" in line)
    assert "composer" in line
    assert "promoted" in line
