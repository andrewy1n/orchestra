from __future__ import annotations

from orchestra import views
from orchestra.canon.types import JsonObject, JsonValue, Record

DESCRIPTION = "R1: Brief quotes the work item.\nR2: Second line of the description."
APPROACH = "Extend the renderer.\n\n- keep sections\n- add orientation"
SPEC_BODY = (
    "## Requirements\n\n"
    "R1: Spec wording of the first requirement.\n"
    "R2: Spec wording of the second requirement.\n\n"
    "## Invariants\n\nSpec invariant."
)
DESIGN_BODY = (
    "## Architecture\n\nArch text.\n\n"
    "## Invariants\n\n- Old records stay valid.\n\n"
    "## Assumptions\n\n- The consumer list is complete.\n\n"
    "## Risks\n\nRisk text."
)


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    body: str = "",
    state: str = "active",
) -> Record:
    return {
        "id": f"id-{record_type}-{subject}",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-05T00:00:00Z",
        "body": body,
    }


def _work_item(**payload: JsonValue) -> Record:
    base: JsonObject = {"title": "Build it", "phase": "p1", "kind": "deliver", "effort": "alpha"}
    base.update(payload)
    return _record(
        "score:work-item",
        "build-it",
        base,
        f"## Description\n\n{DESCRIPTION}\n\n## Approach\n\n{APPROACH}",
        "in_progress",
    )


def _orientation(text: str) -> str:
    start = text.index("## Orientation")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def test_brief_quotes_description_and_approach() -> None:
    text = views.render_brief("build-it", [_work_item()])
    block = _orientation(text)
    assert DESCRIPTION in block
    assert APPROACH in block
    assert "## Work Item" in text
    assert "## Acceptance Criteria" in text


def test_brief_quotes_requirements_from_spec() -> None:
    spec = _record(
        "score:specification",
        "p1",
        {"phase": "p1", "effort": "alpha", "requirements": ["R1", "R2"]},
        SPEC_BODY,
    )
    block = _orientation(views.render_brief("build-it", [_work_item(requirements=["R1"]), spec]))
    assert "- R1: Spec wording of the first requirement." in block
    assert "R2" not in block.split("### Requirements")[1]


def test_brief_quotes_requirement_from_description_without_spec() -> None:
    block = _orientation(views.render_brief("build-it", [_work_item(requirements=["R2"])]))
    assert "- R2: Second line of the description." in block.split("### Requirements")[1]


def test_brief_quotes_design_and_decisions() -> None:
    design = _record(
        "score:design",
        "p1",
        {"phase": "p1", "effort": "alpha", "decisions": ["pick-x"]},
        DESIGN_BODY,
    )
    decision = _record(
        "score:decision",
        "pick-x",
        {"choice": "Use X", "alternatives": "Y", "phase": "p1", "effort": "alpha"},
        state="current",
    )
    other = _record(
        "score:decision",
        "pick-z",
        {"choice": "Use Z", "alternatives": "Y", "phase": "p1", "effort": "alpha"},
        state="current",
    )
    block = _orientation(
        views.render_brief("build-it", [_work_item(decisions=["pick-x"]), design, decision, other])
    )
    assert "- Old records stay valid." in block
    assert "- The consumer list is complete." in block
    assert "Arch text." not in block
    assert "Risk text." not in block
    assert "- pick-x: Use X" in block
    assert "pick-z" not in block


def test_brief_shows_assignee_and_write_root() -> None:
    block = _orientation(
        views.render_brief("build-it", [_work_item(assignee="agent-1", write_root="/tmp/wt")])
    )
    assert "**assignee**: agent-1" in block
    assert "**write_root**: /tmp/wt" in block
    bare = _orientation(views.render_brief("build-it", [_work_item()]))
    assert "assignee" not in bare
    assert "write_root" not in bare


def test_brief_acceptances_filtered_by_phase() -> None:
    def acceptance(subject: str, phase: str, effort: str) -> Record:
        return _record(
            "score:acceptance",
            subject,
            {"method": "tdd", "phase": phase, "effort": effort, "verify_command": "x"},
        )

    text = views.render_brief(
        "build-it",
        [
            _work_item(),
            acceptance("build-it", "p1", "alpha"),
            acceptance("build-it-other-phase", "p2", "alpha"),
            acceptance("build-it-other-effort", "p1", "beta"),
        ],
    )
    assert "### build-it\n" in text.split("## Acceptance Criteria")[1]
    assert "build-it-other-phase" not in text
    assert "build-it-other-effort" not in text
