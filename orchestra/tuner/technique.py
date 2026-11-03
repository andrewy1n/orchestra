from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypeGuard, runtime_checkable

from orchestra.canon.project_config import ProjectConfig
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


class ClaimReplayTechnique(Protocol):
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
) -> dict[str, TestOutcome]:
    from orchestra.canon.extensions import resolve_plugin
    from orchestra.canon.project_config import load_project_config_at_revision

    config = load_project_config_at_revision(root, revision)
    plugin_id = config.replay_technique
    registration = resolve_plugin("tuner.verify", plugin_id)
    factory = registration.load()
    if not callable(factory):
        raise TechniqueContractError(f"verification plugin {plugin_id!r} is not constructible")
    plugin = factory()
    return run_claim_replay(
        plugin,
        ReplayRequest(root=Path(root), revision=revision, test_ids=test_ids, runner=runner),
    )


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
