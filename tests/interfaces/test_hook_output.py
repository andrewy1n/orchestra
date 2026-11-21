import io
from pathlib import Path

import pytest
from hook_support import FORMATS, REFERENCE_ERROR, hook_input, run_hook, set_store_errors

from orchestra import cli
from orchestra.canon.project import Project
from orchestra.stage import hooks


def start_context(fmt: str, out: dict[str, object]) -> str:
    if fmt == "--claude":
        assert set(out) == {"hookSpecificOutput"}
        inner = out["hookSpecificOutput"]
        assert isinstance(inner, dict)
        assert inner["hookEventName"] == "SessionStart"
        ctx = inner["additionalContext"]
    else:
        assert set(out) == {"additional_context"}
        ctx = out["additional_context"]
    assert isinstance(ctx, str)
    return ctx


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_start_on_clean_store_emits_protocol_and_handoff(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = run_hook(monkeypatch, capsys, "hook-start", fmt, hook_input(fmt, repo.project_root))

    assert code == 0
    assert out is not None
    ctx = start_context(fmt, out)
    assert ctx.startswith(hooks.PROTOCOL)
    assert "# Project Handoff" in ctx
    assert "Goal of alpha" in ctx
    assert ctx.endswith("\n")


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_start_with_store_errors_still_injects_handoff(
    fmt: str,
    repo: Project,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])

    code, out = run_hook(monkeypatch, capsys, "hook-start", fmt, hook_input(fmt, repo.project_root))

    assert code == 0
    assert out is not None
    ctx = start_context(fmt, out)
    assert "# Project Handoff" in ctx
    assert "session-start failed" not in ctx


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_start_without_store_prints_nothing(
    fmt: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    result = run_hook(monkeypatch, capsys, "hook-start", fmt, hook_input(fmt, empty))

    assert result == (0, None)


@pytest.mark.parametrize("command", ["hook-start", "hook-stop"])
def test_hook_rejects_non_object_input(
    command: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("[1]"))

    code = cli.main([command, "--claude"])

    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "invalid hook input" in captured.err
