from __future__ import annotations

from collections.abc import Iterator, Mapping

from orchestra.conductor.briefs.render import (
    SKILL_TABLE,
    STEP_TABLE,
    BriefContext,
    Section,
    render_brief,
)

PHASE = "phase-test"
EFFORT = "effort-test"
ADAPTERS = ("github-pr", "claude")
UNFILLED_PLACEHOLDERS = (
    "<current-phase-slug>",
    "<phase-slug>",
    "<effort-slug>",
    "<focus>",
)
DANGLING_FILE_NAMES = (
    "phase-end.md",
    "retry-loop.md",
    "reviewer.md",
    "assess.md",
    "close-batch.md",
    "land-github-pr.md",
    "record-mechanics.md",
    "verification-policy.md",
    "task-shapes.md",
    "oracle-author.md",
    "execute-mechanics.md",
    "planning-mechanics.md",
    "intent-qa.md",
    "ensure-store.md",
    "kinds-and-focus.md",
    "verify-mechanics.md",
)


def _briefs(table: Mapping[str, tuple[Section, ...]]) -> Iterator[tuple[str, str]]:
    stages = {section.stage for sections in table.values() for section in sections}
    stages.add(None)
    for step in table:
        for stage in stages:
            for adapter in ADAPTERS:
                context = BriefContext(step, PHASE, EFFORT, stage, adapter, "full")
                yield f"{step}/{stage}/{adapter}", render_brief(context, table=table)


def test_no_unfilled_placeholders() -> None:
    for label, text in (*_briefs(STEP_TABLE), *_briefs(SKILL_TABLE)):
        for placeholder in UNFILLED_PLACEHOLDERS:
            assert placeholder not in text, f"{label}: {placeholder}"


def test_no_dangling_file_pointers() -> None:
    for label, text in (*_briefs(STEP_TABLE), *_briefs(SKILL_TABLE)):
        assert "references/" not in text, label
        for filename in DANGLING_FILE_NAMES:
            assert filename not in text, f"{label}: {filename}"
