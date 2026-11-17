from __future__ import annotations

from pathlib import Path

from canon_support import create, make_project, seed_effort

from orchestra import views
from orchestra.canon.project import Project
from orchestra.canon.types import Record

EFFORT = "alpha"
STAMPS = {
    "first": "2026-01-01T00:00:01Z",
    "second": "2026-01-01T00:00:02Z",
    "third": "2026-01-01T00:00:03Z",
}


def _store(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, EFFORT)
    return project


def _acceptance(project: Project, subject: str = "ac-1") -> Record:
    return create(
        project,
        "score:acceptance",
        subject,
        {
            "requirement": "R1",
            "method": "manual",
            "phase": "p1",
            "effort": EFFORT,
            "verify_command": "true",
        },
    )


def _run(project: Project, acceptance: Record, signed_by: str) -> Record:
    return create(
        project,
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["subject"],
            "revision": "abc123",
            "result": "pass",
            "effort": EFFORT,
            "method": "manual",
            "signed_by": signed_by,
        },
    )


def _finding(project: Project, subject: str, effort: str) -> Record:
    return create(
        project,
        "tuner:finding",
        subject,
        {
            "claim": "A human decision is required.",
            "basis": "Evidence",
            "invalidated_when": "A human resolves it.",
            "effort": effort,
            "needs": "human",
        },
    )


def _question(project: Project) -> Record:
    return create(
        project,
        "score:continuity-question",
        EFFORT,
        {"owner": "human", "blocking": True, "scope": EFFORT},
    )


def _stamped(project: Project, stamps: dict[str, str]) -> list[Record]:
    records = views.load_records(project)
    for record in records:
        if record["id"] in stamps:
            record["recorded_at"] = stamps[record["id"]]
    return records


def _handoff(records: list[Record]) -> str:
    return views.render_view(views.HANDOFF, records)


def _hook_text(records: list[Record]) -> str:
    return "\n".join(text for _, text in views.hook_handoff_sections(records))


def test_r11_handoff_lists_each_gate_kind_under_its_heading(tmp_path: Path) -> None:
    project = _store(tmp_path)
    question = _question(project)
    finding = _finding(project, "needs-answer", EFFORT)
    run = _run(project, _acceptance(project), "")
    text = _handoff(views.load_records(project))

    assert "## alpha" in text
    for heading, record in (
        ("### Blocking Question", question),
        ("### Needs Human", finding),
        ("### Unsigned Manual Check", run),
    ):
        section = text.split(heading, 1)[1].split("###", 1)[0]
        assert record["subject"] in section
        assert record["id"] in section


def test_r11_hook_sections_list_each_gate_kind_under_its_heading(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _question(project)
    _finding(project, "needs-answer", EFFORT)
    _run(project, _acceptance(project), "")
    text = _hook_text(views.load_records(project))

    assert "### Blocking Question" in text
    assert "### Needs Human" in text
    assert "### Unsigned Manual Check" in text
    assert "needs-answer" in text


def test_r11_handoff_omits_signed_gate_kinds(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _run(project, _acceptance(project), "alice")
    text = _handoff(views.load_records(project))

    assert "### Unsigned Manual Check" not in text


def test_r11_handoff_omits_unsigned_run_after_later_signed_run(tmp_path: Path) -> None:
    project = _store(tmp_path)
    acceptance = _acceptance(project)
    unsigned = _run(project, acceptance, "")
    signed = _run(project, acceptance, "alice")
    records = _stamped(project, {unsigned["id"]: STAMPS["first"], signed["id"]: STAMPS["second"]})

    assert "### Unsigned Manual Check" not in _handoff(records)
    assert "### Unsigned Manual Check" not in _hook_text(records)


def test_r11_handoff_lists_unsigned_run_after_later_signed_run_is_reversed(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    acceptance = _acceptance(project)
    signed = _run(project, acceptance, "alice")
    unsigned = _run(project, acceptance, "")
    records = _stamped(project, {signed["id"]: STAMPS["first"], unsigned["id"]: STAMPS["second"]})
    text = _handoff(records)

    section = text.split("### Unsigned Manual Check", 1)[1].split("###", 1)[0]
    assert unsigned["id"] in section
    assert signed["id"] not in section


def test_r11_handoff_omits_corrected_unsigned_run(tmp_path: Path) -> None:
    project = _store(tmp_path)
    acceptance = _acceptance(project)
    unsigned = _run(project, acceptance, "")
    project.correct(unsigned["id"], payload={**unsigned["payload"], "signed_by": "alice"})
    text = _handoff(views.load_records(project))

    assert "### Unsigned Manual Check" not in text
    assert unsigned["id"] not in text


def test_r12_handoff_lists_needs_human_finding_without_effort(tmp_path: Path) -> None:
    project = _store(tmp_path)
    finding = _finding(project, "effortless-question", EFFORT)
    records = views.load_records(project)
    for record in records:
        if record["id"] == finding["id"]:
            record["payload"] = {**record["payload"], "effort": ""}

    text = _handoff(records)
    assert "### Needs Human" in text
    assert finding["id"] in text.split("### Needs Human", 1)[1]

    hook = _hook_text(records)
    assert "### Needs Human" in hook
    assert "effortless-question" in hook
