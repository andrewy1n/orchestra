from pathlib import Path

import pytest
from hook_support import FORMATS, hook_input, run_hook

from orchestra.canon.project import Project
from orchestra.canon.workspace import Access, Workspace

COMMANDS = ("hook-start", "hook-stop")


def snapshot(path: Path) -> set[Path]:
    return set(path.rglob("*"))


def record_access(monkeypatch: pytest.MonkeyPatch) -> list[Access]:
    requested: list[Access] = []
    original = Workspace.open

    def recording_open(self: Workspace) -> Project:
        requested.append(self.access)
        return original(self)

    monkeypatch.setattr(Workspace, "open", recording_open)
    return requested


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize("fmt", FORMATS)
def test_no_store_hook_prints_nothing_and_creates_no_store(
    command: str,
    fmt: str,
    tmp_path: Path,
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty = tmp_path / "nowhere" / "deep"
    empty.mkdir(parents=True)
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    before = snapshot(tmp_path)
    home_before = snapshot(isolated_home)

    result = run_hook(monkeypatch, capsys, command, fmt, hook_input(fmt, empty))

    assert result == (0, None)
    assert snapshot(tmp_path) == before
    assert snapshot(isolated_home) == home_before
    assert not (empty / ".canon").exists()


@pytest.mark.parametrize("fmt", FORMATS)
def test_stop_reads_only_opens_store_read_access(
    fmt: str,
    repo: Project,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requested = record_access(monkeypatch)

    result = run_hook(monkeypatch, capsys, "hook-stop", fmt, hook_input(fmt, repo.project_root))

    assert result == (0, {})
    assert requested == [Access.READ]


@pytest.mark.parametrize("fmt", FORMATS)
def test_start_opens_store_write_access(
    fmt: str,
    repo: Project,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requested = record_access(monkeypatch)

    code, out = run_hook(monkeypatch, capsys, "hook-start", fmt, hook_input(fmt, repo.project_root))

    assert code == 0
    assert out is not None
    assert requested == [Access.WRITE]
