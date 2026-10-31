"""CLI tests for orchestra idea capture (R2, R4, R5, R6, R9)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import helpers as h
import pytest
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


def test_r2_idea_command_writes_title_as_first_body_line(store, cli):
    title = "Body Title Line"
    result = run_orchestra(store, "idea", title)
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject="body-title-line")
    assert len(ideas) == 1, ideas
    first_line = ideas[0]["body"].splitlines()[0]
    assert first_line == f"# {title}"


def test_r4_idea_command_sets_effort_flag(store, cli, defs):
    h.create_generic_record(cli, defs, "score:effort", subject="composer")
    result = run_orchestra(store, "idea", "Effort Tagged", "--effort", "composer")
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject="effort-tagged")
    assert len(ideas) == 1, ideas
    assert ideas[0]["payload"].get("effort") == "composer"


def test_r5_idea_command_sets_source_flag(store, cli):
    source = "standup notes"
    result = run_orchestra(store, "idea", "Sourced Idea", "--source", source)
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject="sourced-idea")
    assert len(ideas) == 1, ideas
    assert ideas[0]["payload"].get("source") == source


def test_r6_idea_command_appends_body_file(store, cli, tmp_path):
    appendix = "Detail from a file.\nSecond line."
    body_file = tmp_path / "extra.md"
    body_file.write_text(appendix, encoding="utf-8")
    title = "File Body"
    result = run_orchestra(
        store,
        "idea",
        title,
        "--body-file",
        str(body_file),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    ideas = _list_ideas(cli, subject="file-body")
    assert len(ideas) == 1, ideas
    expected = f"# {title}\n\n{appendix}"
    assert ideas[0]["body"].rstrip("\n") == expected.rstrip("\n")


def test_r9_idea_command_refuses_unknown_effort(store, cli):
    before = _list_ideas(cli)
    result = run_orchestra(store, "idea", "No Effort", "--effort", "missing-effort")
    assert result.returncode != 0, result.stdout + result.stderr
    assert "invalid choice: 'idea'" not in result.stderr
    after = _list_ideas(cli)
    assert after == before


@pytest.fixture()
def defs(resolved_contract):
    return h.record_defs_by_id(resolved_contract)
