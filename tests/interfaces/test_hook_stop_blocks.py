from pathlib import Path

import pytest
from hook_support import (
    FORMATS,
    NEW_ERROR,
    REFERENCE_ERROR,
    hook_input,
    run_hook,
    set_store_errors,
)

from orchestra.canon.project import Project


def block_message(fmt: str, out: dict[str, object] | None) -> str:
    assert out is not None
    if fmt == "--claude":
        assert out["decision"] == "block"
        message = out["reason"]
    else:
        assert set(out) == {"followup_message"}
        message = out["followup_message"]
    assert isinstance(message, str)
    return message


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_on_clean_store_allows_stop(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run_hook(monkeypatch, capsys, "hook-stop", fmt, hook_input(fmt, repo.project_root))

    assert result == (0, {})


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_without_baseline_blocks_on_any_error(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])

    code, out = run_hook(monkeypatch, capsys, "hook-stop", fmt, hook_input(fmt, repo.project_root))

    assert code == 0
    message = block_message(fmt, out)
    assert message.startswith("Session-end store check failed:")
    assert REFERENCE_ERROR in message


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_allows_errors_present_at_session_start(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])
    stdin = hook_input(fmt, repo.project_root)
    run_hook(monkeypatch, capsys, "hook-start", fmt, stdin)

    result = run_hook(monkeypatch, capsys, "hook-stop", fmt, stdin)

    assert result == (0, {})


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_blocks_on_error_added_since_session_start(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stdin = hook_input(fmt, repo.project_root)
    set_store_errors(monkeypatch, [REFERENCE_ERROR])
    run_hook(monkeypatch, capsys, "hook-start", fmt, stdin)
    set_store_errors(monkeypatch, [REFERENCE_ERROR, NEW_ERROR])

    code, out = run_hook(monkeypatch, capsys, "hook-stop", fmt, stdin)

    assert code == 0
    message = block_message(fmt, out)
    assert NEW_ERROR in message
    assert REFERENCE_ERROR not in message
    assert "1 error(s) already present when this session started are not shown." in message


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_blocks_on_new_error_after_clean_start(
    fmt: str, repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stdin = hook_input(fmt, repo.project_root)
    run_hook(monkeypatch, capsys, "hook-start", fmt, stdin)
    set_store_errors(monkeypatch, [NEW_ERROR])

    _, out = run_hook(monkeypatch, capsys, "hook-stop", fmt, stdin)

    message = block_message(fmt, out)
    assert NEW_ERROR in message
    assert "already present" not in message


def test_hook_stop_claude_skips_check_when_stop_hook_active(
    repo: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])
    stdin = hook_input("--claude", repo.project_root, stop_hook_active=True)

    assert run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin) == (0, {})


@pytest.mark.parametrize("loop_count", [1, 3])
def test_hook_stop_cursor_skips_check_when_loop_count_positive(
    loop_count: int,
    repo: Project,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])
    stdin = hook_input("--cursor", repo.project_root, loop_count=loop_count)

    assert run_hook(monkeypatch, capsys, "hook-stop", "--cursor", stdin) == (0, {})


@pytest.mark.parametrize("status", ["aborted", "error"])
def test_hook_stop_cursor_skips_check_unless_completed(
    status: str,
    repo: Project,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    set_store_errors(monkeypatch, [REFERENCE_ERROR])
    stdin = hook_input("--cursor", repo.project_root, status=status)

    assert run_hook(monkeypatch, capsys, "hook-stop", "--cursor", stdin) == (0, {})


@pytest.mark.parametrize("fmt", FORMATS)
def test_hook_stop_without_store_prints_nothing(
    fmt: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    result = run_hook(monkeypatch, capsys, "hook-stop", fmt, hook_input(fmt, empty))

    assert result == (0, None)
