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


STEP_TABLE: Mapping[str, tuple[Section, ...]] = {}


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
