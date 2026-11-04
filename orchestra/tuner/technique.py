from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypeGuard, runtime_checkable

from orchestra.canon.extensions import (
    PluginRegistration,
    compute_execution_identity,
    resolve_plugin,
    validate_plugin_config,
)
from orchestra.canon.project_config import ProjectConfig, load_project_config_at_revision
from orchestra.canon.types import JsonObject

Verdict = Literal["pass", "fail", "error", "skip"]
TestOutcome = Literal["passed", "assertion_failed", "errored", "not_run"]


class TechniqueContractError(ValueError):
    """A verification technique does not meet its result or replay contract."""


@dataclass(frozen=True)
class VerificationRequest:
    plugin_id: str
    stage: str
    revision: str
    config: JsonObject
    inputs: JsonObject


@dataclass(frozen=True)
class ReplayRequest:
    root: Path
    revision: str
    test_ids: tuple[str, ...]
    runner: tuple[str, ...]


@dataclass(frozen=True)
class TechniqueResult:
    verdict: Verdict
    output: JsonObject


@runtime_checkable
class VerificationTechnique(Protocol):
    def validate_config(self, config: ProjectConfig) -> None: ...

    def execution_definition(self, config: ProjectConfig) -> JsonObject: ...

    def validate_result(self, result: TechniqueResult) -> None: ...


class ClaimReplayTechnique(VerificationTechnique, Protocol):
    def replay(self, request: ReplayRequest) -> Mapping[str, TestOutcome]: ...


def validate_technique_result(technique: VerificationTechnique, result: object) -> TechniqueResult:
    if not isinstance(result, TechniqueResult):
        raise TechniqueContractError("technique result must use TechniqueResult")
    if result.verdict not in ("pass", "fail", "error", "skip"):
        raise TechniqueContractError(f"invalid technique verdict: {result.verdict!r}")
    if not _is_json_object(result.output):
        raise TechniqueContractError("technique output must be structured JSON")
    technique.validate_result(result)
    return result


def run_claim_replay(
    technique: object,
    request: ReplayRequest,
) -> dict[str, TestOutcome]:
    if not _supports_claim_replay(technique):
        raise TechniqueContractError("claim replay requires a replay-capable technique")
    outcomes = technique.replay(request)
    if not _is_mapping(outcomes):
        raise TechniqueContractError("replay outcomes must be a mapping")
    if set(outcomes) != set(request.test_ids):
        raise TechniqueContractError("replay outcomes must cover each requested test exactly once")
    valid = ("passed", "assertion_failed", "errored", "not_run")
    result: dict[str, TestOutcome] = {}
    for test_id in request.test_ids:
        outcome = outcomes[test_id]
        if outcome not in valid:
            raise TechniqueContractError(f"invalid replay outcome for {test_id!r}: {outcome!r}")
        result[test_id] = outcome
    return result


def replay_at_revision(
    root: Path | str,
    revision: str,
    test_ids: tuple[str, ...],
    runner: tuple[str, ...],
    *,
    trusted_config_revision: str | None = None,
    plugin_id: str | None = None,
    expected_identity: JsonObject | None = None,
) -> dict[str, TestOutcome]:
    config_revision = trusted_config_revision or revision
    config, selected_plugin_id, registration, plugin = _load_replay_technique(
        root, config_revision, plugin_id
    )
    definition = plugin.execution_definition(config)
    identity = compute_execution_identity(
        registration.descriptor,
        config.verify_config.get(selected_plugin_id, {}),
        definition,
    ).payload
    if expected_identity is not None and identity != expected_identity:
        raise TechniqueContractError("replay technique identity differs from trusted config")
    return run_claim_replay(
        plugin,
        ReplayRequest(root=Path(root), revision=revision, test_ids=test_ids, runner=runner),
    )


def replay_identity_at_revision(
    root: Path | str,
    revision: str,
) -> tuple[str, JsonObject]:
    config, plugin_id, registration, plugin = _load_replay_technique(root, revision, None)
    identity = compute_execution_identity(
        registration.descriptor,
        config.verify_config.get(plugin_id, {}),
        plugin.execution_definition(config),
    )
    return plugin_id, identity.payload


def _load_replay_technique(
    root: Path | str,
    revision: str,
    plugin_id: str | None,
) -> tuple[ProjectConfig, str, PluginRegistration, ClaimReplayTechnique]:
    config = load_project_config_at_revision(root, revision)
    selected_plugin_id = plugin_id or config.replay_technique
    registration = resolve_plugin("tuner.verify", selected_plugin_id)
    factory = registration.load()
    if not callable(factory):
        raise TechniqueContractError(
            f"verification plugin {selected_plugin_id!r} is not constructible"
        )
    technique = factory()
    if not isinstance(technique, VerificationTechnique):
        raise TechniqueContractError(
            f"verification plugin {selected_plugin_id!r} has an invalid technique contract"
        )
    validate_plugin_config(
        selected_plugin_id,
        registration.descriptor.config_shape,
        config.verify_config.get(selected_plugin_id, {}),
    )
    technique.validate_config(config)
    if not _supports_claim_replay(technique):
        raise TechniqueContractError("claim replay requires a replay-capable technique")
    return config, selected_plugin_id, registration, technique


def _supports_claim_replay(technique: object) -> TypeGuard[ClaimReplayTechnique]:
    return callable(getattr(technique, "replay", None))


def _is_json_value(value: object) -> bool:
    try:
        encoded = json.dumps(value, allow_nan=False)
        decoded: object = json.loads(encoded)
    except (TypeError, ValueError):
        return False
    return type(decoded) is type(value) and decoded == value


def _is_json_object(value: object) -> bool:
    return isinstance(value, dict) and _is_json_value(value)  # pyright: ignore[reportUnknownArgumentType]  # Plugin object keys remain dynamic until JSON serialization validates them.


def _is_mapping(value: object) -> bool:
    return isinstance(value, Mapping)
