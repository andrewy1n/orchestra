from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from orchestra.canon.extensions import PluginCatalogError, resolve_plugin, validate_plugin_config
from orchestra.canon.project_config import ProjectConfig, load_project_config
from orchestra.canon.types import JsonObject


@dataclass(frozen=True)
class LandRequest:
    root: Path
    proof_packet: str
    base: str
    remote: str
    poll_interval_s: float
    timeout_s: float
    config: JsonObject


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
        from orchestra.conductor.github_pr import open_pull_request

        result = open_pull_request(
            request.root,
            request.proof_packet,
            base=request.base,
            remote=request.remote,
            poll_interval_s=request.poll_interval_s,
            timeout_s=request.timeout_s,
            adapter_config=request.config,
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
