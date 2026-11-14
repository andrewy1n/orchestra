from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.types import JsonValue
from orchestra.cli import main
from orchestra.conductor.briefs import render

EFFORT = "brief-cli-effort"
READY_PHASE = "ready-phase"
BLOCKED_PHASE = "blocked-phase"
STEP = "spec"
BRIEF_TEXT = "Write the specification for {phase}."
PHASE_BODY = (
    "## Problem\nMeet the contract.\n"
    "## Requirements\nR1: Preserve the workflow contract.\n"
    "## Approach\nUse the reviewed design.\n"
    "## Exit criteria\nVerify the result.\n"
)


@pytest.fixture(autouse=True)
def _test_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(render, "STEP_TABLE", {STEP: (render.Section("test-section"),)})
    monkeypatch.setattr(render, "_read", lambda name, source: BRIEF_TEXT)


def _invoke(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    try:
        code = main(["workflow", *args, "--store", str(root)])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _seed_run(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    project = make_project(root)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Brief CLI", "kind": "deliver"},
    )
    for ordinal, (slug, depends_on) in enumerate(
        ((READY_PHASE, []), (BLOCKED_PHASE, [READY_PHASE])), start=1
    ):
        dependencies: list[JsonValue] = list(depends_on)
        project.create(
            record_type="score:phase",
            subject=slug,
            payload={
                "title": slug,
                "ordinal": ordinal,
                "effort": EFFORT,
                "weight": "light",
                "depends_on": dependencies,
            },
            body=PHASE_BODY,
        )
    selector = f"{READY_PHASE},{BLOCKED_PHASE}"
    _, output, _ = _invoke(root, capsys, "preview", EFFORT, selector, "phase", "--json")
    token = json.loads(output)["snapshot_token"]
    code, output, error = _invoke(
        root, capsys, "start", EFFORT, selector, "phase", "--snapshot-token", token, "--json"
    )
    assert code == 0, output + error
    return str(json.loads(output)["run"]["subject"])


def _actions(
    root: Path, capsys: pytest.CaptureFixture[str], run: str, *extra: str
) -> dict[str, dict[str, str]]:
    code, output, error = _invoke(root, capsys, "next", run, "--json", *extra)
    assert code == 0, output + error
    return {action["phase"]: action for action in json.loads(output)["actions"]}


def test_blocked_action_has_no_brief(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run = _seed_run(tmp_path, capsys)

    actions = _actions(tmp_path, capsys, run)

    assert actions[READY_PHASE]["state"] == "ready"
    assert actions[READY_PHASE]["brief"]
    assert actions[BLOCKED_PHASE]["state"] == "blocked"
    assert "brief" not in actions[BLOCKED_PHASE]
    assert actions[BLOCKED_PHASE]["reason"]


def test_next_no_brief_omits_the_brief_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = _seed_run(tmp_path, capsys)

    actions = _actions(tmp_path, capsys, run, "--no-brief")

    assert actions[READY_PHASE]["state"] == "ready"
    assert "brief" not in actions[READY_PHASE]


def test_brief_command_matches_next(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run = _seed_run(tmp_path, capsys)
    next_brief = _actions(tmp_path, capsys, run)[READY_PHASE]["brief"]

    code, output, error = _invoke(tmp_path, capsys, "brief", READY_PHASE, STEP)

    assert code == 0, output + error
    assert next_brief
    assert output.rstrip("\n") == next_brief


def test_blocked_step_exits_non_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run = _seed_run(tmp_path, capsys)
    reason = _actions(tmp_path, capsys, run)[BLOCKED_PHASE]["reason"]

    code, output, error = _invoke(tmp_path, capsys, "brief", BLOCKED_PHASE, STEP)

    assert code != 0
    assert reason in error
    assert output == ""
