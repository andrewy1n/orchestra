"""Required project config loading and commit-pinned runner argv."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestra.canon.project_config import (
    DEFAULT_EXECUTOR_SETTINGS,
    DEFAULT_LONE_TASK_INLINE_MINUTES,
    DEFAULT_RUNNER,
    ProjectConfigError,
    executor_settings_at,
    load_project_config,
    load_project_config_at_revision,
)


def _config_text(
    runner: tuple[str, ...] = DEFAULT_RUNNER,
    *,
    stage: str = "phase",
    plugins: tuple[str, ...] = ("unit", "review"),
    small_wave_budget_minutes: int | None = None,
) -> str:
    plugin_values = json.dumps(plugins)
    runner_values = json.dumps(runner)
    text = (
        f"[verify.stages]\n{stage} = {plugin_values}\n\n[verify.unit]\nrunner = {runner_values}\n"
    )
    if small_wave_budget_minutes is not None:
        text += f"\n[execute]\nsmall_wave_budget_minutes = {small_wave_budget_minutes}\n"
    return text


def test_small_wave_budget_defaults_to_fifteen_minutes(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(_config_text(), encoding="utf-8")

    assert load_project_config(tmp_path).small_wave_budget_minutes == 15


def test_small_wave_budget_loads_from_execute_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text(small_wave_budget_minutes=24), encoding="utf-8"
    )

    assert load_project_config(tmp_path).small_wave_budget_minutes == 24


@pytest.mark.parametrize("value", ["true", "-1", "1.5", '"15"'])
def test_invalid_small_wave_budget_is_rejected(tmp_path: Path, value: str) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text() + f"\n[execute]\nsmall_wave_budget_minutes = {value}\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectConfigError, match="small_wave_budget_minutes"):
        load_project_config(tmp_path)


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
        f"[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n\n"
        '[verify.external]\nendpoint = "https://example.test"\n\n'
        '[land]\nadapter = "external-land"\nmerge = "human"\n'
        '[land.config]\nregion = "west"\n',
        encoding="utf-8",
    )

    config = load_project_config(tmp_path)

    assert config.verify_config["external"] == {"endpoint": "https://example.test"}
    assert config.land_adapter == "external-land"
    assert config.land_config == {"region": "west"}


def test_unit_runner_is_required_for_each_project_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["external"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ProjectConfigError, match=r"verify\.unit"):
        load_project_config(tmp_path)


def test_replay_technique_is_selected_from_project_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["external"]\n'
        f"[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n"
        '[verify.replay]\ntechnique = "replay-external"\n',
        encoding="utf-8",
    )

    assert load_project_config(tmp_path).replay_technique == "replay-external"


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


def test_lone_task_inline_minutes_defaults_to_constant(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(_config_text(), encoding="utf-8")

    assert (
        load_project_config(tmp_path).lone_task_inline_minutes == DEFAULT_LONE_TASK_INLINE_MINUTES
    )


def test_lone_task_inline_minutes_loads_from_execute_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text() + "\n[execute]\nlone_task_inline_minutes = 5\n", encoding="utf-8"
    )

    assert load_project_config(tmp_path).lone_task_inline_minutes == 5


@pytest.mark.parametrize("value", ["true", "-1", "1.5", '"10"'])
def test_lone_task_inline_minutes_invalid_value_is_rejected(tmp_path: Path, value: str) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text() + f"\n[execute]\nlone_task_inline_minutes = {value}\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectConfigError, match="lone_task_inline_minutes"):
        load_project_config(tmp_path)


def test_executor_settings_at_gives_defaults_when_config_is_missing(tmp_path: Path) -> None:
    assert executor_settings_at(tmp_path) == DEFAULT_EXECUTOR_SETTINGS


def test_executor_settings_at_reads_both_thresholds(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text()
        + "\n[execute]\nsmall_wave_budget_minutes = 7\nlone_task_inline_minutes = 5\n",
        encoding="utf-8",
    )

    settings = executor_settings_at(tmp_path)

    assert (settings.small_wave_budget_minutes, settings.lone_task_inline_minutes) == (7, 5)


def test_executor_settings_at_rejects_an_invalid_config(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        _config_text() + "\n[execute]\nlone_task_inline_minutes = -1\n", encoding="utf-8"
    )

    with pytest.raises(ProjectConfigError, match="lone_task_inline_minutes"):
        executor_settings_at(tmp_path)
