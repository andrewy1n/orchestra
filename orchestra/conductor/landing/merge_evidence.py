from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from orchestra.canon.extensions import resolve_plugin, validate_plugin_config
from orchestra.canon.project import Project
from orchestra.canon.project_config import ProjectConfig, load_project_config
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor import gate
from orchestra.conductor.landing.landing import latest_landing, phase_place, proof_packet
from orchestra.score.planning.phase import Phase, current_phase_model
from orchestra.tools import Git

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
    try:
        factory = registration.load()
    except (ImportError, AttributeError) as error:
        raise EvidenceError(f"cannot load CI evidence adapter {name!r}: {error}") from error
    if not callable(factory):
        raise EvidenceError(f"CI evidence adapter {name!r} is not constructible")
    try:
        adapter = factory()
    except TypeError as error:
        raise EvidenceError(f"cannot construct CI evidence adapter {name!r}: {error}") from error
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


def _phase_evidence(
    project: Project, records: list[Record], phase: Phase, work: Path, head: str
) -> tuple[str, list[str], str | None]:
    if not head:
        return "unresolved", ["pull request head is unavailable"], None
    packet = proof_packet(records, phase, head)
    if packet is None:
        return "blocked", [f"no phase proof packet for {head}"], None
    if Git(work).head() != head:
        return "blocked", ["phase worktree HEAD differs from the pull request head"], packet.id
    terms = gate.gate_terms(project, phase.subject, head_worktree=work)
    missing = gate.format_missing(gate.missing_terms(terms))
    if Git(work).head() != head:
        return "unresolved", ["phase worktree head changed during refresh"], packet.id
    return ("blocked" if missing else "pass"), missing, packet.id


def _ci_evidence(snapshot: EvidenceSnapshot) -> tuple[bool, bool, list[str]]:
    blockers = [snapshot.unresolved] if snapshot.unresolved else []
    if not snapshot.required_checks and not blockers:
        blockers.append("no required CI checks are configured")
    unresolved = bool(blockers)
    failed = False
    results = {evidence.check: evidence for evidence in snapshot.results}
    for check in snapshot.required_checks:
        label = f"{check.name} ({check.source})" if check.source else check.name
        result = results.get(check)
        if result is None or result.state == "missing":
            blockers.append(f"{label}: required CI result is missing")
            unresolved = True
        elif result.revision != snapshot.head:
            blockers.append(f"{label}: CI result covers {result.revision}")
            unresolved = True
        elif result.state == "pending":
            blockers.append(f"{label}: required CI check is pending")
            unresolved = True
        elif result.state == "fail":
            blockers.append(f"{label}: required CI check failed")
            failed = True
    return failed, unresolved, blockers


def refresh_recommendation(project: Project, phase_slug: str) -> JsonObject:
    records = project.records()
    phase = current_phase_model(phase_slug, records)
    if phase is None:
        raise EvidenceError(f"unknown phase {phase_slug!r}")
    landing = latest_landing(records, phase_slug)
    if landing is None or not landing.url:
        raise EvidenceError(f"no pull request recorded for {phase_slug!r}")

    work = phase_place(phase, project.project_root).worktree
    if not work.is_dir():
        raise EvidenceError(f"phase worktree {work} is missing")
    config = load_project_config(work)
    provider = config.merge_evidence_adapter
    if provider is None:
        raise EvidenceError("merge_evidence.adapter must be configured")
    snapshot = collect_evidence(work, landing.url, config)

    phase_status, phase_blockers, packet = _phase_evidence(
        project, records, phase, work, snapshot.head
    )
    ci_failed, ci_unresolved, ci_blockers = _ci_evidence(snapshot)
    if ci_unresolved or phase_status == "unresolved":
        recommendation = "unresolved"
    elif phase_status == "blocked" or ci_failed:
        recommendation = "blocked"
    else:
        recommendation = "ready"

    checks: list[JsonValue] = [
        {
            "name": result.check.name,
            "source": result.check.source,
            "state": result.state,
            "revision": result.revision,
            "run_url": result.run_url,
        }
        for result in snapshot.results
    ]
    required: list[JsonValue] = [
        {"name": check.name, "source": check.source} for check in snapshot.required_checks
    ]
    output: JsonObject = {
        "phase": phase_slug,
        "provider": provider,
        "pull_request": landing.url,
        "head": snapshot.head,
        "phase_verification": phase_status,
        "proof_packet": packet,
        "required_checks": required,
        "checks": checks,
        "recommendation": recommendation,
        "blockers": [*phase_blockers, *ci_blockers],
    }
    observation = project.create(
        record_type="conductor:ci-observation",
        subject=phase_slug,
        payload={
            "phase": phase_slug,
            "effort": phase.effort,
            "provider": provider,
            "url": landing.url,
            "revision": snapshot.head,
            "recommendation": recommendation,
        },
        body=json.dumps(output, indent=2, sort_keys=True),
    )
    output["observation"] = observation["id"]
    return output
