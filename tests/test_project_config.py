"""Required project config loading and commit-pinned runner argv."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestra.canon.project_config import (
    DEFAULT_RUNNER,
    ProjectConfigError,
    load_project_config,
    load_project_config_at_revision,
)


def _config_text(
    runner: tuple[str, ...] = DEFAULT_RUNNER,
    *,
    stage: str = "phase",
    plugins: tuple[str, ...] = ("unit", "review"),
) -> str:
    plugin_values = json.dumps(plugins)
    runner_values = json.dumps(runner)
    return (
        f"[verify.stages]\n{stage} = {plugin_values}\n\n[verify.unit]\nrunner = {runner_values}\n"
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(root: Path) -> None:
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def test_missing_config_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ProjectConfigError, match="required project config is missing"):
        load_project_config(tmp_path)


def test_malformed_toml_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text("[verify\n", encoding="utf-8")
    with pytest.raises(ProjectConfigError, match="invalid TOML"):
        load_project_config(tmp_path)


def test_registered_plugin_id_is_loaded_from_project_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text(plugins=("unit", "external")),
        encoding="utf-8",
    )
    assert load_project_config(tmp_path).stages["phase"] == ("unit", "external")


def test_plugin_parameters_are_read_from_scope_tables(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["external"]\n\n'
        '[verify.external]\nendpoint = "https://example.test"\n\n'
        '[land]\nadapter = "external-land"\nmerge = "human"\n'
        '[land.config]\nregion = "west"\n',
        encoding="utf-8",
    )

    config = load_project_config(tmp_path)

    assert config.verify_config["external"] == {"endpoint": "https://example.test"}
    assert config.land_adapter == "external-land"
    assert config.land_config == {"region": "west"}


def test_non_unit_verification_does_not_require_unit_runner(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["external"]\n',
        encoding="utf-8",
    )

    assert load_project_config(tmp_path).stages["phase"] == ("external",)


def test_invalid_stage_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text(stage="release"),
        encoding="utf-8",
    )
    with pytest.raises(ProjectConfigError, match="invalid verification stage"):
        load_project_config(tmp_path)


def test_runner_argv_is_loaded_from_requested_commit(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _init_repo(root)
    first_runner = ("python3", "-m", "pytest", "--first", "{tests}", "--junitxml={report}")
    (root / "orchestra.toml").write_text(_config_text(first_runner), encoding="utf-8")
    first = _commit(root, "first runner")
    second_runner = ("uv", "run", "pytest", "--second", "{tests}", "--junitxml={report}")
    (root / "orchestra.toml").write_text(_config_text(second_runner), encoding="utf-8")
    second = _commit(root, "second runner")
    (root / "orchestra.toml").write_text(
        _config_text(("pytest", "--dirty", "{tests}", "--junitxml={report}")),
        encoding="utf-8",
    )

    assert load_project_config_at_revision(root, first).runner == first_runner
    assert load_project_config_at_revision(root, second).runner == second_runner
    assert load_project_config(root).runner == (
        "pytest",
        "--dirty",
        "{tests}",
        "--junitxml={report}",
    )
