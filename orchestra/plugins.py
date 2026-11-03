"""Stage dispatch for the built-in verification plugins."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from orchestra.canon.extensions import (
    PluginCatalogError,
    PluginDescriptor,
    list_plugins,
    resolve_plugin,
)
from orchestra.canon.project_config import (
    ProjectConfig,
    StageName,
    load_project_config_at_revision,
)
from orchestra.conductor.reviewer import ReviewerRecord, validate_reviewer_output
from orchestra.tuner.manifest import resolve_commit, runner_digest
from orchestra.tuner.runner import run_tests


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
    output: Mapping[str, str] | str


@runtime_checkable
class BuiltinPlugin(Protocol):
    def run(self, config: ProjectConfig, context: PluginContext) -> PluginResult: ...


class UnitPlugin:
    plugin_id: str = "unit"

    def run(self, config: ProjectConfig, context: PluginContext) -> PluginResult:
        if not context.tests:
            raise ValueError("unit plugin requires at least one test id")
        outcomes = run_tests(context.root, context.tests, config.runner)
        result = "pass" if all(outcome == "passed" for outcome in outcomes.values()) else "fail"
        return PluginResult(
            plugin_id=self.plugin_id,
            stage=context.stage,
            revision=context.revision,
            result=result,
            runner_digest=runner_digest(config.runner),
            output=outcomes,
        )


class ReviewPlugin:
    plugin_id: str = "review"

    def run(self, config: ProjectConfig, context: PluginContext) -> PluginResult:
        del config
        if context.reviewer_output is None or not context.reviewer_output.strip():
            raise ValueError("review plugin requires structured output from the host reviewer")
        parsed = validate_reviewer_output(context.reviewer_output)
        verdict = parsed["verdict"]
        return PluginResult(
            plugin_id=self.plugin_id,
            stage=context.stage,
            revision=context.revision,
            result="pass" if verdict == "PASS" else "fail",
            runner_digest=None,
            output={"verdict": verdict, "reviewer_output": context.reviewer_output},
        )


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
            factory = resolve_plugin("tuner.verify", plugin_id).load()
        except PluginCatalogError as exc:
            raise ValueError(str(exc)) from exc
        if not callable(factory):
            raise ValueError(f"verification plugin {plugin_id!r} is not constructible")
        plugin = factory()
        if not isinstance(plugin, BuiltinPlugin):
            raise ValueError(f"verification plugin {plugin_id!r} has no run method")
        results.append(plugin.run(config, pinned_context))
    return tuple(results)


def registered_plugin_ids() -> tuple[str, ...]:
    return tuple(sorted(descriptor.plugin_id for descriptor in resolve_plugin_catalog()))


def resolve_plugin_catalog() -> tuple[PluginDescriptor, ...]:
    return list_plugins("tuner.verify")
