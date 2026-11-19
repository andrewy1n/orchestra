from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.extensions import PluginCatalogError, resolve_plugin, validate_plugin_config
from orchestra.canon.project import Project
from orchestra.canon.project_config import ProjectConfig, load_project_config
from orchestra.canon.types import JsonObject
from orchestra.conductor import gate
from orchestra.conductor.github_pr import GitHubClient, GitHubPRError, open_pull_request
from orchestra.conductor.landing import (
    LANDING,
    describe_phase,
    landing_payload,
    proof_packet_record,
    pull_request_title,
)
from orchestra.score.lookups import current_phase
from orchestra.tools import Git


@dataclass(frozen=True)
class LandRequest:
    root: Path
    proof_packet: str
    base: str
    remote: str
    poll_interval_s: float
    timeout_s: float
    config: JsonObject
    title: str = ""
    description: Mapping[str, str] = field(default_factory=lambda: {})
    client: GitHubClient | None = None


@dataclass(frozen=True)
class LandingCheck:
    name: str
    status: str
    conclusion: str | None


@dataclass(frozen=True)
class LandingResult:
    result: str
    number: int
    url: str
    head_sha: str
    checks: tuple[LandingCheck, ...]
    statuses: tuple[str, ...]


@runtime_checkable
class LandAdapter(Protocol):
    def run(self, request: LandRequest) -> LandingResult: ...


class NoneAdapter:
    def run(self, request: LandRequest) -> LandingResult:
        del request
        return LandingResult("skipped", 0, "", "", (), ())


class GitHubPRAdapter:
    def run(self, request: LandRequest) -> LandingResult:
        if request.client is None:
            raise GitHubPRError("the github-pr adapter needs a gh client")
        result = open_pull_request(
            request.root,
            request.proof_packet,
            base=request.base,
            remote=request.remote,
            poll_interval_s=request.poll_interval_s,
            timeout_s=request.timeout_s,
            title=request.title or None,
            description=request.description,
            client=request.client,
        )
        return LandingResult(
            result=result.result,
            number=result.number,
            url=result.url,
            head_sha=result.head_sha,
            checks=tuple(
                LandingCheck(check.name, check.status, check.conclusion) for check in result.checks
            ),
            statuses=result.statuses,
        )


def dispatch_land(
    root: Path | str,
    proof_packet: str,
    *,
    base: str = "main",
    remote: str = "origin",
    poll_interval_s: float = 10,
    timeout_s: float = 1800,
    title: str = "",
    description: Mapping[str, str] | None = None,
    client: GitHubClient | None = None,
) -> LandingResult:
    project_root = Path(root)
    config: ProjectConfig = load_project_config(project_root)
    if not config.land_configured:
        raise ValueError("land.adapter must be configured before landing")
    try:
        registration = resolve_plugin("conductor.land", config.land_adapter)
        validate_plugin_config(
            config.land_adapter,
            registration.descriptor.config_shape,
            config.land_config,
        )
        factory = registration.load()
    except PluginCatalogError as exc:
        raise ValueError(str(exc)) from exc
    if not callable(factory):
        raise ValueError(f"landing adapter {config.land_adapter!r} is not constructible")
    adapter = factory()
    if not isinstance(adapter, LandAdapter):
        raise ValueError(f"landing adapter {config.land_adapter!r} has no run method")
    result = _run_adapter(
        adapter,
        LandRequest(
            root=project_root,
            proof_packet=proof_packet,
            base=base,
            remote=remote,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            config=dict(config.land_config),
            title=title,
            description=dict(description or {}),
            client=client,
        ),
    )
    if not isinstance(result, LandingResult):
        raise ValueError("landing adapter must return LandingResult")
    if result.result not in ("success", "fail", "blocked", "skipped"):
        raise ValueError(f"landing adapter returned invalid result: {result.result!r}")
    if not _valid_landing_fields(result):
        raise ValueError("landing adapter returned malformed structured output")
    return result


def _run_adapter(adapter: LandAdapter, request: LandRequest) -> object:
    return adapter.run(request)


def _valid_landing_fields(value: object) -> bool:
    if not isinstance(value, LandingResult):
        return False
    return (
        value.number >= 0
        and _is_string(value.url)
        and _is_string(value.head_sha)
        and all(_is_string(status) for status in value.statuses)
        and all(_is_landing_check(check) for check in value.checks)
    )


def _is_string(value: object) -> bool:
    return isinstance(value, str)


def _is_landing_check(value: object) -> bool:
    return isinstance(value, LandingCheck)


class LandGateError(RuntimeError):
    def __init__(self, phase: str, lines: Sequence[str]) -> None:
        super().__init__(f"{phase}: " + "; ".join(lines))
        self.phase = phase
        self.lines = tuple(lines)


def land_phase(
    root: Path,
    store_dir: Path | None,
    open_project: Callable[[], Project],
    phase: str,
    work: Path,
    client: GitHubClient,
    *,
    base: str,
    remote: str,
    poll_interval_s: float,
    timeout_s: float,
) -> LandingResult:
    """Gate a phase, land it from `work`, and record the landing unless the result is skipped."""
    missing = gate.missing_terms(
        gate.gate_terms(root, phase, store_dir=store_dir, head_worktree=work)
    )
    if missing:
        raise LandGateError(phase, gate.format_missing(missing))
    project = open_project()
    records = project.records()
    phase_record = current_phase(phase, records)
    if phase_record is None:
        raise StoreError(f"unknown record: no score:phase with subject {phase!r}")
    head = Git(work).head()
    packet = proof_packet_record(records, phase_record, head)
    if packet is None:
        raise ValueError(f"no proof packet for phase {phase!r} at HEAD {head}")
    body = packet.get("body")
    if not isinstance(body, str):
        raise ValueError("phase proof packet has no body")
    result = dispatch_land(
        work,
        body,
        base=base,
        remote=remote,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        title=pull_request_title(phase_record),
        description=describe_phase(phase_record),
        client=client,
    )
    if result.result != "skipped":
        effort = record_payload(packet).get("effort")
        project.create(
            record_type=LANDING,
            subject=phase,
            payload=landing_payload(
                phase,
                result.number,
                result.url,
                result.head_sha,
                result.result,
                effort if isinstance(effort, str) else None,
            ),
        )
    return result
