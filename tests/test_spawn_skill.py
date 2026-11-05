"""Failing oracles for the spawn spec brief and execute-phase dispatch.

R1 compares `orchestra brief` stdout for a temporary work-item with the
brief section of a cursor render. R27, R28, and R29 require execute-phase
steps 5, 6, and 7 to submit render output, send message output, and record
parse output as the execution-report body.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort
from conftest import REPO_ROOT

_SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"
_HEADERS = ("## Brief", "## Orientation", "## Kind", "## Write root")
_STEP = re.compile(r"(?m)^(?P<number>\d+)\. ")


def _env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CANON_STORE", "ORCHESTRA_STORE"}
    }
    prior = env.get("PYTHONPATH", "")
    parts = [str(REPO_ROOT)]
    if prior:
        parts.append(prior)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(parts))
    return env


def _run(
    args: list[str], *, stdin: str | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    work = cwd
    cleanup = False
    if work is None:
        work = Path(tempfile.mkdtemp(prefix="spawn-oracle-"))
        cleanup = True
    try:
        return subprocess.run(
            [sys.executable, "-m", "orchestra.cli", *args],
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(work),
            env=_env(),
            check=False,
        )
    finally:
        if cleanup:
            shutil.rmtree(work, ignore_errors=True)


def _spec(brief: str) -> dict[str, object]:
    capabilities: dict[str, object] = {"readonly": False}
    return {
        "subject": "build-widget",
        "brief": brief,
        "orientation": "Territory: north.\nQuote the requirement verbatim.\n",
        "kind": "deliver",
        "verification": False,
        "write_root": "/repo/.worktrees/phase-one--build-widget",
        "capabilities": capabilities,
    }


def _prompt(stdout: str) -> str:
    assert stdout.lstrip().startswith("{"), stdout
    loaded: object = json.loads(stdout)
    assert isinstance(loaded, dict)
    prompt = loaded.get("prompt")
    assert isinstance(prompt, str)
    cursor = 0
    for header in _HEADERS:
        marker = f"{header}\n"
        found = prompt.find(marker, cursor)
        assert found >= 0
        assert found == 0 or prompt[found - 1] == "\n"
        cursor = found + len(marker)
    return prompt


def _brief_section(prompt: str) -> str:
    start = prompt.find("## Brief\n")
    assert start >= 0
    body_start = start + len("## Brief\n")
    end = prompt.find("\n## Orientation\n", body_start)
    assert end >= 0
    return prompt[body_start:end]


def _step(number: int) -> str:
    text = _SKILL.read_text(encoding="utf-8")
    matches = list(_STEP.finditer(text))
    body = ""
    for index, match in enumerate(matches):
        if int(match.group("number")) != number:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start() : end]
        break
    assert body
    return body


def test_r1_brief(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CANON_STORE", raising=False)
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    name = f"spawn-oracle-{uuid.uuid4().hex}"
    assert not (Path.home() / ".canon" / name).exists()
    root = tmp_path / name
    project = make_project(root)
    assert project.store_path.resolve().is_relative_to(root.resolve())
    seed_effort(project, "alpha")
    create(
        project,
        "score:work-item",
        "build-widget",
        {
            "title": "Build the widget",
            "phase": "p1",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
        },
    )
    brief_run = _run(["brief", "build-widget"], cwd=root)
    assert brief_run.returncode == 0, brief_run.stderr
    brief = brief_run.stdout
    assert brief.startswith("# Brief: build-widget")
    assert "\n## Orientation\n" not in brief
    rendered = _run(
        ["spawn", "render", "--provider", "cursor", "--adapter-version", "1"],
        stdin=json.dumps(_spec(brief)),
        cwd=root,
    )
    assert rendered.returncode == 0, rendered.stderr
    section = _brief_section(_prompt(rendered.stdout))
    assert brief in section
    assert section.strip() == brief.strip()
    skill = re.sub(r"\s+", " ", _SKILL.read_text(encoding="utf-8"))
    assert "stdout of `orchestra brief" in skill


def test_r27_submit_render() -> None:
    step = re.sub(r"\s+", " ", _step(5))
    assert "orchestra spawn render" in step
    assert "submit" in step


def test_r28_send_message() -> None:
    step = re.sub(r"\s+", " ", _step(6))
    assert "orchestra spawn message" in step
    start = step.index("orchestra spawn message")
    window = step[max(0, start - 80) : start + len("orchestra spawn message") + 80]
    assert "send" in window


def test_r29_record_parse() -> None:
    step = re.sub(r"\s+", " ", _step(7))
    assert "orchestra spawn parse" in step
    start = step.index("orchestra spawn parse")
    window = step[max(0, start - 160) : start + 200]
    assert "execution-report" in window
    assert "body" in window
