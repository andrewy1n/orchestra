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
from orchestra.conductor.reviewer import ReviewerRecord, validate_reviewer_output
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
    review_records: tuple[ReviewerRecord, ...] = ()
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
        return TechniqueResult(verdict=result, output=outcomes)

    def validate_result(self, result: TechniqueResult) -> None:
        if not isinstance(result.output, dict) or any(
            not isinstance(test_id, str)
            or outcome not in ("passed", "assertion_failed", "errored", "not_run")
            for test_id, outcome in result.output.items()
        ):
            raise ValueError("unit plugin output must map test ids to valid outcomes")

    def replay(self, request: ReplayRequest) -> dict[str, str]:
        return run_tests(request.root, request.test_ids, request.runner)


class ReviewPlugin:
    plugin_id: str = "review"

    def validate_config(self, config: ProjectConfig) -> None:
        del config

    def execution_definition(self, config: ProjectConfig) -> JsonObject:
        del config
        return {"reviewer_contract": 1}

    def run(self, config: ProjectConfig, context: PluginContext) -> TechniqueResult:
        del config
        if context.reviewer_output is None or not context.reviewer_output.strip():
            raise ValueError("review plugin requires structured output from the host reviewer")
        parsed = validate_reviewer_output(context.reviewer_output)
        verdict = parsed["verdict"]
        return TechniqueResult(
            verdict="pass" if verdict == "PASS" else "fail",
            output={"verdict": verdict, "reviewer_output": context.reviewer_output},
        )

    def validate_result(self, result: TechniqueResult) -> None:
        if not isinstance(result.output, dict):
            raise ValueError("review plugin output must be an object")
        verdict = result.output.get("verdict")
        reviewer_output = result.output.get("reviewer_output")
        if verdict not in ("PASS", "NEEDS_WORK") or not isinstance(reviewer_output, str):
            raise ValueError("review plugin output does not contain a valid reviewer result")
        if (result.verdict == "pass") != (verdict == "PASS"):
            raise ValueError("review plugin verdict does not match the reviewer result")


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
    if not isinstance(argv, list) or any(not isinstance(arg, str) for arg in argv):
        return None
    return runner_digest(argv)
