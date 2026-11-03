"""Stage dispatch for the built-in verification plugins."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from orchestra.canon.extensions import (
    PluginCatalogError,
    PluginDescriptor,
    compute_execution_identity,
    list_plugins,
    resolve_plugin,
)
from orchestra.canon.project_config import (
    ProjectConfig,
    StageName,
    load_project_config_at_revision,
)
from orchestra.canon.types import JsonObject
from orchestra.tuner.manifest import resolve_commit, runner_digest
from orchestra.tuner.runner import run_tests
from orchestra.tuner.technique import (
    ReplayRequest,
    TechniqueResult,
    VerificationTechnique,
    validate_technique_result,
)


@dataclass(frozen=True)
class PluginContext:
    root: Path
    stage: StageName
    revision: str
    tests: tuple[str, ...] = ()
    review_records: tuple[JsonObject, ...] = ()
    phase_diff: str = ""
    base_revision: str = "main"
    phase_head: str = "HEAD"
    reviewer_output: str | None = None


@dataclass(frozen=True)
class PluginResult:
    plugin_id: str
    stage: StageName
    revision: str
    result: str
    runner_digest: str | None
    output: JsonObject
    execution_identity: JsonObject
    execution_digest: str


@runtime_checkable
class BuiltinPlugin(VerificationTechnique, Protocol):
    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult: ...


class UnitPlugin:
    plugin_id: str = "unit"

    def validate_config(self, config: ProjectConfig) -> None:
        del config

    def execution_definition(self, config: ProjectConfig) -> JsonObject:
        return {"runner_argv": list(config.runner)}

    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult:
        if not context.tests:
            raise ValueError("unit plugin requires at least one test id")
        outcomes = run_tests(context.root, context.tests, config.runner)
        result = "pass" if all(outcome == "passed" for outcome in outcomes.values()) else "fail"
        output: JsonObject = {test_id: outcome for test_id, outcome in outcomes.items()}
        return TechniqueResult(verdict=result, output=output)

    def validate_result(self, result: TechniqueResult) -> None:
        if any(
            outcome not in ("passed", "assertion_failed", "errored", "not_run")
            for outcome in result.output.values()
        ):
            raise ValueError("unit plugin output must map test ids to valid outcomes")

    def replay(self, request: ReplayRequest) -> dict[str, str]:
        return run_tests(request.root, request.test_ids, request.runner)


def dispatch_plugins(
    context: PluginContext,
) -> tuple[PluginResult, ...]:
    """Run configured built-ins for one stage in declaration order."""
    revision = resolve_commit(context.root, context.revision)
    head = resolve_commit(context.root, "HEAD")
    if revision != head:
        raise ValueError("plugin execution worktree HEAD must match the target revision")
    config = load_project_config_at_revision(context.root, revision)
    plugin_ids = config.stages.get(context.stage)
    if plugin_ids is None:
        raise ValueError(f"verification stage is not configured: {context.stage}")
    pinned_context = PluginContext(
        root=context.root,
        stage=context.stage,
        revision=revision,
        tests=context.tests,
        review_records=context.review_records,
        phase_diff=context.phase_diff,
        base_revision=context.base_revision,
        phase_head=context.phase_head,
        reviewer_output=context.reviewer_output,
    )
    results: list[PluginResult] = []
    for plugin_id in plugin_ids:
        try:
            registration = resolve_plugin("tuner.verify", plugin_id)
            factory = registration.load()
        except PluginCatalogError as exc:
            raise ValueError(str(exc)) from exc
        if not callable(factory):
            raise ValueError(f"verification plugin {plugin_id!r} is not constructible")
        plugin = factory()
        if not isinstance(plugin, BuiltinPlugin):
            raise ValueError(f"verification plugin {plugin_id!r} has no run method")
        plugin.validate_config(config)
        definition = plugin.execution_definition(config)
        parameters = config.verify_config.get(plugin_id, {})
        identity = compute_execution_identity(registration.descriptor, parameters, definition)
        technique_result = validate_technique_result(plugin, plugin.run(config, pinned_context))
        results.append(
            PluginResult(
                plugin_id=plugin_id,
                stage=context.stage,
                revision=revision,
                result=technique_result.verdict,
                runner_digest=_runner_digest(definition),
                output=technique_result.output,
                execution_identity=identity.payload,
                execution_digest=identity.digest,
            )
        )
    return tuple(results)


def registered_plugin_ids() -> tuple[str, ...]:
    return tuple(sorted(descriptor.plugin_id for descriptor in resolve_plugin_catalog()))


def resolve_plugin_catalog() -> tuple[PluginDescriptor, ...]:
    return list_plugins("tuner.verify")


def _runner_digest(definition: JsonObject) -> str | None:
    argv = definition.get("runner_argv")
    if not isinstance(argv, list):
        return None
    arguments = [arg for arg in argv if isinstance(arg, str)]
    if len(arguments) != len(argv):
        return None
    return runner_digest(arguments)
