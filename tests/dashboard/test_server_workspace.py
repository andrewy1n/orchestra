from __future__ import annotations

from pathlib import Path

import pytest
import uvicorn
from canon_support import make_project

from dashboard.backend.server import __main__ as server_main
from dashboard.backend.server import app as server_app
from orchestra.canon.project import Project
from orchestra.canon.workspace import Workspace


class _Launch:
    def __init__(self) -> None:
        self.targets: list[Project] = []
        self.runs = 0


@pytest.fixture
def launch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> _Launch:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in ("CANON_STORE", "ORCHESTRA_STORE", "CANON_READONLY"):
        monkeypatch.delenv(name, raising=False)
    seen = _Launch()

    def fake_create_app(target: Project) -> object:
        seen.targets.append(target)
        return object()

    def fake_run(*_args: object, **_kwargs: object) -> None:
        seen.runs += 1

    monkeypatch.setattr(server_main, "create_app", fake_create_app)
    monkeypatch.setattr(server_app, "create_app", fake_create_app)
    monkeypatch.setattr(uvicorn, "run", fake_run)
    return seen


def test_server_not_ready_reports_searched_paths_and_exits_1(
    launch: _Launch,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    start = tmp_path / "empty" / "child"
    start.mkdir(parents=True)
    monkeypatch.chdir(start)

    code = server_main.main([])

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert code == 1
    assert "store_not_ready" in output
    assert str(start.resolve()) in output
    assert str(start.resolve().parent) in output
    assert launch.runs == 0
    assert launch.targets == []


def test_server_same_store_as_workspace_resolve(
    launch: _Launch, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = make_project(tmp_path / "repo")
    nested = project.project_root / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    code = server_main.main([])

    expected = Workspace.resolve(nested).open().store_path
    assert code == 0
    assert launch.runs == 1
    assert [target.store_path for target in launch.targets] == [expected]
