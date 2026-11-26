"""Project policy and runner configuration from orchestra.toml."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeGuard

from orchestra.canon.types import JsonObject, JsonValue
from orchestra.tools.errors import ToolError, ToolNotFoundError
from orchestra.tools.git import Git

CONFIG_PATH = "orchestra.toml"
DEFAULT_SMALL_WAVE_BUDGET_MINUTES = 15
DEFAULT_LONE_TASK_INLINE_MINUTES = 10
StageName = Literal["task", "phase", "milestone"]
PluginName = str
SUITE_MODES = ("none", "smoke", "full", "external")
SUITE_GATES = ("required", "advisory", "deferred")
DEFAULT_RUNNER = (
    "python3",
    "-m",
    "pytest",
    "-o",
    "junit_family=xunit1",
    "{tests}",
    "--junitxml={report}",
)


class ProjectConfigError(ValueError):
    """The project config is missing, malformed, or invalid."""


@dataclass(frozen=True)
class ExecutorSettings:
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES
    lone_task_inline_minutes: int = DEFAULT_LONE_TASK_INLINE_MINUTES


DEFAULT_EXECUTOR_SETTINGS = ExecutorSettings()


@dataclass(frozen=True)
class SuiteConfig:
    mode: str
    command: str
    gate: str


@dataclass(frozen=True)
class ProjectConfig:
    stages: Mapping[StageName, tuple[PluginName, ...]]
    runner: tuple[str, ...]
    suite: SuiteConfig
    land_adapter: str
    land_configured: bool
    merge_policy: str
    verify_config: Mapping[str, JsonObject]
    land_config: JsonObject
    replay_technique: str
    small_wave_budget_minutes: int
    merge_evidence_adapter: str | None = None
    merge_evidence_config: JsonObject = field(default_factory=dict)
    lone_task_inline_minutes: int = DEFAULT_LONE_TASK_INLINE_MINUTES

    @property
    def executor_settings(self) -> ExecutorSettings:
        return ExecutorSettings(self.small_wave_budget_minutes, self.lone_task_inline_minutes)


def load_project_config(root: Path | str) -> ProjectConfig:
    """Load the required project config from the working tree."""
    path = Path(root) / CONFIG_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProjectConfigError(f"required project config is missing: {path}") from exc
    except OSError as exc:
        raise ProjectConfigError(f"cannot read project config: {path}") from exc
    return _parse_project_config(text, source=str(path))


def load_project_config_at_revision(root: Path | str, revision: str) -> ProjectConfig:
    """Load orchestra.toml from a committed revision, ignoring worktree edits."""
    try:
        git = Git(Path(root))
        commit = git.resolve(revision)
        if commit is None:
            raise ProjectConfigError(f"cannot resolve commit {revision}")
        config_result = git.run("show", f"{commit}:{CONFIG_PATH}")
        if config_result.returncode != 0:
            raise ProjectConfigError(f"cannot load {CONFIG_PATH} at commit {revision}")
    except ToolNotFoundError as exc:
        raise ProjectConfigError("git executable not found while loading project config") from exc
    except ToolError as exc:
        raise ProjectConfigError(exc.stderr.strip() or str(exc)) from exc
    return _parse_project_config(config_result.stdout, source=f"{CONFIG_PATH} at {commit}")


def _parse_project_config(text: str, *, source: str) -> ProjectConfig:
    try:
        raw = _load_toml(text)
    except ValueError as exc:
        raise ProjectConfigError(f"invalid TOML in {source}: {exc}") from exc
    root = _table(raw, source)
    verify = _table(root.get("verify"), "verify")
    stages_raw = _table(verify.get("stages"), "verify.stages")
    stages = _parse_stages(stages_raw)
    unit_value = verify.get("unit")
    unit = _table(unit_value, "verify.unit")
    runner_value = unit.get("runner")
    if runner_value is None:
        raise ProjectConfigError("verify.unit.runner is required")
    runner = _string_list(runner_value, "verify.unit.runner")
    if not runner:
        raise ProjectConfigError("verify.unit.runner must be a non-empty argv list")
    if runner.count("{tests}") != 1 or not any("{report}" in arg for arg in runner):
        raise ProjectConfigError("verify.unit.runner must include {tests} once and {report}")
    land_value = root.get("land")
    execute = _table(root.get("execute", {}), "execute")
    small_wave_budget_minutes = _parse_small_wave_budget(execute)
    lone_task_inline_minutes = _parse_lone_task_inline(execute)
    evidence_adapter, evidence_config = _parse_merge_evidence(root.get("merge_evidence"))
    return ProjectConfig(
        stages=stages,
        runner=runner,
        suite=_parse_suite(root.get("suite")),
        land_adapter=_parse_land_adapter(land_value),
        land_configured=land_value is not None,
        merge_policy=_parse_merge_policy(land_value),
        verify_config=_parse_verify_config(verify),
        land_config=_parse_land_config(land_value),
        replay_technique=_parse_replay_technique(verify.get("replay")),
        small_wave_budget_minutes=small_wave_budget_minutes,
        merge_evidence_adapter=evidence_adapter,
        merge_evidence_config=evidence_config,
        lone_task_inline_minutes=lone_task_inline_minutes,
    )


def _table(value: object, label: str) -> Mapping[str, object]:
    if not _is_string_mapping(value):
        raise ProjectConfigError(f"{label} must be a TOML table")
    return value


def _load_toml(text: str) -> object:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    return tomllib.loads(text)


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, dict) and all(
        isinstance(key, str)
        for key in value  # pyright: ignore[reportUnknownVariableType]  # TOML parser keys are dynamic until validated.
    )


def _parse_stages(raw: Mapping[str, object]) -> dict[StageName, tuple[PluginName, ...]]:
    allowed_stages = ("task", "phase", "milestone")
    result: dict[StageName, tuple[PluginName, ...]] = {}
    for stage, plugins_value in raw.items():
        if stage not in allowed_stages:
            raise ProjectConfigError(f"invalid verification stage: {stage}")
        plugins = _string_list(plugins_value, f"verify.stages.{stage}")
        if not plugins:
            raise ProjectConfigError(f"verify.stages.{stage} must be a non-empty plugin list")
        if any(not plugin for plugin in plugins):
            raise ProjectConfigError(f"verify.stages.{stage} contains an empty plugin id")
        if len(set(plugins)) != len(plugins):
            raise ProjectConfigError(f"verify.stages.{stage} contains a duplicate plugin")
        result[stage] = plugins
    if not result:
        raise ProjectConfigError("verify.stages must configure at least one stage")
    return result


def _parse_verify_config(verify: Mapping[str, object]) -> Mapping[str, JsonObject]:
    return {
        plugin_id: _json_object(value, f"verify.{plugin_id}")
        for plugin_id, value in verify.items()
        if plugin_id not in ("stages", "replay")
    }


def _parse_merge_evidence(value: object) -> tuple[str | None, JsonObject]:
    if value is None:
        return None, {}
    raw = _table(value, "merge_evidence")
    adapter = raw.get("adapter")
    if not isinstance(adapter, str) or not adapter.strip():
        raise ProjectConfigError("merge_evidence.adapter must be a non-empty plugin id")
    return adapter, _json_object(raw.get("config", {}), "merge_evidence.config")


def _parse_land_config(value: object) -> JsonObject:
    if value is None:
        return {}
    raw = _table(value, "land")
    config = raw.get("config", {})
    return _json_object(config, "land.config")


def _json_object(value: object, label: str) -> JsonObject:
    raw = _table(value, label)
    return {key: _json_value(item, f"{label}.{key}") for key, item in raw.items()}


def _json_value(value: object, label: str) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, list):
        return [_json_value(item, label) for item in value]  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]  # TOML values are dynamic until validated.
    if _is_string_mapping(value):
        result: JsonObject = {}
        for key, item in value.items():
            result[key] = _json_value(item, f"{label}.{key}")
        return result
    if isinstance(value, dict):
        raise ProjectConfigError(f"{label} contains a non-string key")
    raise ProjectConfigError(f"{label} must contain only JSON values")


def _parse_replay_technique(value: object) -> str:
    if value is None:
        return "unit"
    raw = _table(value, "verify.replay")
    technique = raw.get("technique", "unit")
    if not isinstance(technique, str) or not technique:
        raise ProjectConfigError("verify.replay.technique must be a non-empty plugin id")
    return technique


def _parse_suite(value: object) -> SuiteConfig:
    if value is None:
        return SuiteConfig(mode="none", command="", gate="required")
    raw = _table(value, "suite")
    mode = raw.get("mode", "none")
    command = raw.get("command", "")
    gate = raw.get("gate", "required")
    if not isinstance(mode, str) or mode not in SUITE_MODES:
        raise ProjectConfigError("suite.mode must be none, smoke, full, or external")
    if not isinstance(command, str):
        raise ProjectConfigError("suite.command must be a string")
    if mode in ("smoke", "full") and not command.strip():
        raise ProjectConfigError(f"suite.command must be non-empty for mode {mode!r}")
    if not isinstance(gate, str) or gate not in SUITE_GATES:
        raise ProjectConfigError("suite.gate must be required, advisory, or deferred")
    return SuiteConfig(mode=mode, command=command, gate=gate)


def _parse_small_wave_budget(execute: Mapping[str, object]) -> int:
    value = execute.get("small_wave_budget_minutes", DEFAULT_SMALL_WAVE_BUDGET_MINUTES)
    if type(value) is not int or value < 0:
        raise ProjectConfigError("execute.small_wave_budget_minutes must be a non-negative integer")
    return value


def _parse_lone_task_inline(execute: Mapping[str, object]) -> int:
    value = execute.get("lone_task_inline_minutes", DEFAULT_LONE_TASK_INLINE_MINUTES)
    if type(value) is not int or value < 0:
        raise ProjectConfigError("execute.lone_task_inline_minutes must be a non-negative integer")
    return value


def _parse_land_adapter(value: object) -> str:
    if value is None:
        return "none"
    raw = _table(value, "land")
    adapter = raw.get("adapter", "none")
    if not isinstance(adapter, str) or not adapter:
        raise ProjectConfigError("land.adapter must be a non-empty plugin id")
    return adapter


def _parse_merge_policy(value: object) -> str:
    if value is None:
        return "human"
    raw = _table(value, "land")
    merge = raw.get("merge", "human")
    if not isinstance(merge, str) or merge != "human":
        raise ProjectConfigError("land.merge must be human")
    return merge


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if not _is_string_list(value):
        raise ProjectConfigError(f"{label} must be a list of strings")
    return tuple(value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(item, str)
        for item in value  # pyright: ignore[reportUnknownVariableType]  # TOML parser values are dynamic until validated.
    )
