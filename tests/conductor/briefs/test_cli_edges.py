from __future__ import annotations

import json
from pathlib import Path

import pytest
from conductor_support import EFFORT, PHASE, Cli, seed

from orchestra.cli import main
from orchestra.conductor.briefs import render

SKILLS = ("init", "engage", "triage-ideas", "analyze-sessions")


def _invoke(store: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    try:
        code = main(["workflow", *args, "--store", str(store)])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _parse_object(output: str) -> dict[str, object]:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        pytest.fail(f"stdout is not JSON: {exc}: {output[:80]!r}")
    assert isinstance(parsed, dict), parsed
    return parsed


def _start_spec(store: Path, capsys: pytest.CaptureFixture[str]) -> str:
    _, output, _ = _invoke(store, capsys, "preview", EFFORT, PHASE, "spec", "--json")
    token = json.loads(output)["snapshot_token"]
    code, output, error = _invoke(
        store, capsys, "start", EFFORT, PHASE, "spec", "--snapshot-token", token, "--json"
    )
    assert code == 0, output + error
    return str(json.loads(output)["run"]["subject"])


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_brief_json_prints_object(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, plain, error = _invoke(tmp_path, capsys, "brief", "--skill", skill)
    assert code == 0, error

    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill, "--json")

    assert code == 0, error
    parsed = _parse_object(output)
    assert set(parsed) == {"skill", "brief"}
    assert parsed["skill"] == skill
    assert parsed["brief"] == plain.removesuffix("\n")


@pytest.mark.parametrize("skill", ["spec", "nope"])
def test_skill_brief_json_unknown_name_exits_2(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill, "--json")

    assert code == 2
    assert output == ""
    for name in SKILLS:
        assert name in error


def test_status_does_not_render_briefs(
    store: Path,
    cli: Cli,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed(store, cli)
    run = _start_spec(store, capsys)

    def broken(name: str, source: Path | None) -> str:
        raise ValueError("broken section")

    monkeypatch.setattr(render, "_read", broken)

    code, output, error = _invoke(store, capsys, "status", run, "--json")

    assert code == 0, error
    (action,) = json.loads(output)["actions"]
    assert action["state"] == "ready"
    assert "brief" not in action

    code, output, error = _invoke(store, capsys, "next", run, "--json")

    assert code == 2
    assert output == ""
    assert "broken section" in error


def test_brief_help_notes_prepare_barrier(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["workflow", "brief", "--help"])

    text = " ".join(capsys.readouterr().out.split())
    assert "except in a prepare run, whose barrier next applies and brief does not" in text
