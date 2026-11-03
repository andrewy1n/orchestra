"""Stage dispatch for the built-in verification plugins."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.conductor.reviewer import ReviewerRecord, build_reviewer_brief
from orchestra.project_config import (
    PluginName,
    ProjectConfig,
    StageName,
    load_project_config_at_revision,
)
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


@dataclass(frozen=True)
class PluginResult:
    plugin_id: PluginName
    stage: StageName
    revision: str
    result: str
    runner_digest: str | None
    output: Mapping[str, str] | str


class BuiltinPlugin(Protocol):
    plugin_id: PluginName

    def run(self, config: ProjectConfig, context: PluginContext) -> PluginResult: ...


class UnitPlugin:
    plugin_id: PluginName = "unit"

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
    plugin_id: PluginName = "review"

    def run(self, config: ProjectConfig, context: PluginContext) -> PluginResult:
        del config
        brief = build_reviewer_brief(
            records=context.review_records,
            phase_diff=context.phase_diff,
            base=context.base_revision,
            phase_head=context.phase_head,
        )
        return PluginResult(
            plugin_id=self.plugin_id,
            stage=context.stage,
            revision=context.revision,
            result="ready",
            runner_digest=None,
            output=brief,
        )


BUILTIN_PLUGINS: Mapping[PluginName, BuiltinPlugin] = {
    "unit": UnitPlugin(),
    "review": ReviewPlugin(),
}


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
    )
    return tuple(BUILTIN_PLUGINS[plugin_id].run(config, pinned_context) for plugin_id in plugin_ids)


def registered_plugin_ids() -> tuple[PluginName, ...]:
    """Return the fixed built-in registry ids."""
    return tuple(BUILTIN_PLUGINS)
