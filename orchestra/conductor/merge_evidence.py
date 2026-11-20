from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from orchestra.canon.extensions import resolve_plugin, validate_plugin_config
from orchestra.canon.project_config import ProjectConfig
from orchestra.canon.types import JsonObject

CheckState = Literal["pass", "fail", "pending", "missing"]


@dataclass(frozen=True)
class EvidenceRequest:
    root: Path
    pull_request_url: str
    config: JsonObject


@dataclass(frozen=True)
class RequiredCheck:
    name: str
    source: str = ""


@dataclass(frozen=True)
class CheckEvidence:
    check: RequiredCheck
    state: CheckState
    revision: str
    run_url: str = ""


@dataclass(frozen=True)
class EvidenceSnapshot:
    head: str
    required_checks: tuple[RequiredCheck, ...] = ()
    results: tuple[CheckEvidence, ...] = ()
    unresolved: str = ""


class EvidenceError(ValueError):
    pass


@runtime_checkable
class EvidenceAdapter(Protocol):
    def read(self, request: EvidenceRequest) -> EvidenceSnapshot: ...


def collect_evidence(root: Path, pull_request_url: str, config: ProjectConfig) -> EvidenceSnapshot:
    name = config.merge_evidence_adapter
    if name is None:
        raise EvidenceError("merge_evidence.adapter must be configured")
    registration = resolve_plugin("conductor.merge_evidence", name)
    parameters = config.merge_evidence_config
    validate_plugin_config(name, registration.descriptor.config_shape, parameters)
    factory = registration.load()
    if not callable(factory):
        raise EvidenceError(f"CI evidence adapter {name!r} is not constructible")
    adapter = factory()
    if not isinstance(adapter, EvidenceAdapter):
        raise EvidenceError(f"CI evidence adapter {name!r} has no read method")
    snapshot = _read(adapter, EvidenceRequest(root, pull_request_url, dict(parameters)))
    if not isinstance(snapshot, EvidenceSnapshot):
        raise EvidenceError("CI evidence adapter must return EvidenceSnapshot")
    _validate(snapshot)
    return snapshot


def _read(adapter: EvidenceAdapter, request: EvidenceRequest) -> object:
    return adapter.read(request)


def _validate(snapshot: EvidenceSnapshot) -> None:
    if not snapshot.head and not snapshot.unresolved:
        raise EvidenceError("CI evidence has no pull request head")
    required = set(snapshot.required_checks)
    if len(required) != len(snapshot.required_checks) or any(not item.name for item in required):
        raise EvidenceError("CI evidence has an invalid required check set")
    seen: set[RequiredCheck] = set()
    for result in snapshot.results:
        if result.check not in required or result.check in seen:
            raise EvidenceError("CI evidence has an unexpected or duplicate check result")
        if result.state not in ("pass", "fail", "pending", "missing"):
            raise EvidenceError("CI evidence has an invalid check state")
        if result.state != "missing" and not result.revision:
            raise EvidenceError("CI check evidence has no checked revision")
        seen.add(result.check)
