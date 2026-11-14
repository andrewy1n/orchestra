from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class BriefContext:
    step: str
    phase: str
    effort: str
    stage: str | None
    adapter: str
    weight: str


@dataclass(frozen=True)
class Section:
    name: str
    stage: str | None = None
    when: Callable[[BriefContext], bool] | None = None


def _github_pr(ctx: BriefContext) -> bool:
    return ctx.adapter == "github-pr"


STEP_TABLE: Mapping[str, tuple[Section, ...]] = {
    "spec": (
        Section("ensure-store"),
        Section("kinds-and-focus"),
        Section("intent-qa"),
        Section("verification-policy"),
        Section("spec-process"),
    ),
    "design": (
        Section("ensure-store"),
        Section("kinds-and-focus"),
        Section("intent-qa"),
        Section("design-process"),
    ),
    "tasks": (
        Section("ensure-store"),
        Section("kinds-and-focus"),
        Section("record-mechanics"),
        Section("verification-policy"),
        Section("planning-mechanics"),
        Section("task-shapes"),
        Section("oracle-author"),
        Section("tasks-process"),
    ),
    "verify": (
        Section("verification-policy"),
        Section("record-mechanics"),
        Section("retry-loop"),
        Section("phase-end"),
        Section("verify-mechanics", stage="analyze"),
        Section("assess", stage="analyze"),
        Section("close-batch", stage="analyze"),
        Section("phase-analyze", stage="analyze"),
        Section("phase-suite", stage="suite"),
        Section("phase-reviewer", stage="reviewer"),
        Section("reviewer-prompt", stage="reviewer"),
        Section("phase-gate", stage="gate"),
        Section("phase-proof", stage="proof"),
        Section("phase-close", stage="proof"),
    ),
    "execute": (
        Section("execute-overview"),
        Section("execute-steps"),
        Section("execute-landing"),
        Section("execute-dispatch"),
        Section("execute-evidence"),
        Section("execute-record-vs-bind"),
        Section("execute-do-not"),
        Section("record-mechanics"),
        Section("retry-loop"),
        Section("reviewer-prompt"),
    ),
    "land": (
        Section("land", stage="land"),
        Section("land-github-pr", stage="repair-ci", when=_github_pr),
        Section("retry-loop", stage="repair-ci", when=_github_pr),
        Section("phase-close", stage="close"),
        Section("close-github-pr", stage="close", when=_github_pr),
    ),
}


def _read(name: str, source: Path | None) -> str:
    if source is not None:
        return (source / f"{name}.md").read_text(encoding="utf-8")
    return (
        resources.files("orchestra.conductor.briefs")
        .joinpath("sections")
        .joinpath(f"{name}.md")
        .read_text(encoding="utf-8")
    )


def _selected(section: Section, ctx: BriefContext) -> bool:
    if section.stage is not None and ctx.stage is not None and section.stage != ctx.stage:
        return False
    return section.when is None or section.when(ctx)


def render_brief(
    ctx: BriefContext,
    *,
    table: Mapping[str, tuple[Section, ...]] | None = None,
    source: Path | None = None,
) -> str:
    sections = (STEP_TABLE if table is None else table).get(ctx.step, ())
    parts = [_read(s.name, source).strip() for s in sections if _selected(s, ctx)]
    text = "\n\n".join(parts)
    return text.replace("{phase}", ctx.phase).replace("{effort}", ctx.effort)
