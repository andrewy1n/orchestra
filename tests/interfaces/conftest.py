from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from canon_support import make_project, seed_effort
from interfaces_support import build_world

from orchestra.canon.project import Project

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", autouse=True)
def isolated_home(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    home = tmp_path_factory.mktemp("home")
    patch = pytest.MonkeyPatch()
    patch.setenv("HOME", str(home))
    yield home
    patch.undo()


@pytest.fixture(autouse=True)
def isolated_environment(
    isolated_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ORCHESTRA_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.delenv("CANON_STORE", raising=False)


@pytest.fixture(scope="module")
def shared_world(isolated_home: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_world(tmp_path_factory.mktemp("shared"))


@pytest.fixture
def fresh_world(isolated_home: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_world(tmp_path_factory.mktemp("fresh"))


@pytest.fixture
def wave_world(isolated_home: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_world(tmp_path_factory.mktemp("wave"), wave_started=True)


@pytest.fixture
def bare_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("bare")


@pytest.fixture
def repo(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project
