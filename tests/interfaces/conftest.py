from pathlib import Path

import pytest
from canon_support import make_project, seed_effort

from orchestra.canon.project import Project


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCHESTRA_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CANON_STORE", raising=False)


@pytest.fixture
def repo(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project
