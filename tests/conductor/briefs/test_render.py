from __future__ import annotations

from pathlib import Path

from orchestra.conductor.briefs.render import BriefContext, Section, render_brief


def _ctx(
    step: str = "verify",
    stage: str | None = None,
    adapter: str = "claude",
) -> BriefContext:
    return BriefContext(
        step=step,
        phase="step-briefs",
        effort="workflow-loop",
        stage=stage,
        adapter=adapter,
        weight="normal",
    )


def _sections(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (tmp_path / f"{name}.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_fills_phase_and_effort_placeholders(tmp_path: Path) -> None:
    source = _sections(tmp_path, {"intro": "Run canon show {phase} --effort {effort}."})
    table = {"verify": (Section("intro"),)}

    text = render_brief(_ctx(), table=table, source=source)

    assert "canon show step-briefs --effort workflow-loop." in text
    assert "{phase}" not in text
    assert "{effort}" not in text


def test_brief_holds_only_sections_of_its_own_step(tmp_path: Path) -> None:
    source = _sections(tmp_path, {"v": "VERIFY-BODY", "l": "LAND-BODY"})
    table = {"verify": (Section("v"),), "land": (Section("l"),)}

    text = render_brief(_ctx(step="verify"), table=table, source=source)

    assert "VERIFY-BODY" in text
    assert "LAND-BODY" not in text


def test_sections_render_in_table_order(tmp_path: Path) -> None:
    source = _sections(tmp_path, {"a": "FIRST", "b": "SECOND"})
    table = {"verify": (Section("a"), Section("b"))}

    text = render_brief(_ctx(), table=table, source=source)

    assert text.index("FIRST") < text.index("SECOND")


def test_stage_selects_only_matching_stage_sections(tmp_path: Path) -> None:
    source = _sections(
        tmp_path,
        {"common": "COMMON", "ready": "READY-BODY", "late": "LATE-BODY"},
    )
    table = {
        "verify": (
            Section("common"),
            Section("ready", stage="ready"),
            Section("late", stage="late"),
        )
    }

    text = render_brief(_ctx(stage="ready"), table=table, source=source)

    assert "COMMON" in text
    assert "READY-BODY" in text
    assert "LATE-BODY" not in text


def test_unknown_stage_none_includes_every_stage_section(tmp_path: Path) -> None:
    source = _sections(
        tmp_path,
        {"common": "COMMON", "ready": "READY-BODY", "late": "LATE-BODY"},
    )
    table = {
        "verify": (
            Section("common"),
            Section("ready", stage="ready"),
            Section("late", stage="late"),
        )
    }

    text = render_brief(_ctx(stage=None), table=table, source=source)

    assert "COMMON" in text
    assert "READY-BODY" in text
    assert "LATE-BODY" in text


def test_conditional_section_follows_context(tmp_path: Path) -> None:
    source = _sections(tmp_path, {"base": "BASE", "cursor": "CURSOR-ONLY"})
    table = {
        "verify": (
            Section("base"),
            Section("cursor", when=lambda c: c.adapter == "cursor"),
        )
    }

    on = render_brief(_ctx(adapter="cursor"), table=table, source=source)
    off = render_brief(_ctx(adapter="claude"), table=table, source=source)

    assert "CURSOR-ONLY" in on
    assert "CURSOR-ONLY" not in off
    assert "BASE" in off


def test_same_context_renders_same_text(tmp_path: Path) -> None:
    source = _sections(tmp_path, {"a": "A {phase}", "b": "B {effort}"})
    table = {"verify": (Section("a"), Section("b", stage="x"))}
    ctx = _ctx(stage=None)

    first = render_brief(ctx, table=table, source=source)
    second = render_brief(ctx, table=table, source=source)

    assert first
    assert first == second
