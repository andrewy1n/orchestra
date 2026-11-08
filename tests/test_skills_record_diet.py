"""Skills stop writing derived records and batch their writes through `canon apply`."""

from __future__ import annotations

import json
import re

import helpers as h
from skill_extraction import check_invocation, extract_invocations

DEFS = h.schema_defs()
APPLY_OPS = {"create", "update", "supersede", "correct"}
_HEREDOC = re.compile(r"<<'EOF'\n(.*?)\nEOF\n", re.DOTALL)


def _text(name: str) -> str:
    return h.skill_text(name)


def _skill_md(name: str) -> str:
    reference = {
        "execute": "execute-mechanics.md",
        "tasks": "planning-mechanics.md",
        "verify": "verify-mechanics.md",
    }[name]
    return (h.REPO_ROOT / "skills" / name / "references" / reference).read_text()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _invocations(text: str, subcommand: str, record_type: str) -> list[dict]:
    return [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == subcommand and inv["type"] == record_type
    ]


def _batch_lines(text: str) -> list[dict]:
    lines: list[dict] = []
    for block in _HEREDOC.findall(text):
        for raw in block.splitlines():
            if raw.startswith("{"):
                lines.append(json.loads(raw))
    return lines


def _line_violations(line: dict) -> list[str]:
    inv = {
        "subcommand": line["op"],
        "type": line["type"],
        "transition": line.get("transition"),
        "rels": [],
        "payload": line.get("payload"),
        "raw": json.dumps(line),
    }
    return check_invocation(inv, DEFS)


def _apply_count(text: str) -> int:
    return len(re.findall(r"^canon apply\b", text, re.MULTILINE))


def test_execute_phase_writes_no_assignment() -> None:
    text = _text("execute")
    flat = _flat(text)
    assert not _invocations(text, "create", "conductor:assignment")
    assert "Write no `conductor:assignment`" in flat
    reports = _invocations(text, "create", "conductor:execution-report")
    assert reports
    assert all("assignment" not in (inv["payload"] or {}) for inv in reports)
    amendments = _invocations(text, "create", "conductor:assignment-amendment")
    assert all((inv["payload"] or {}).get("work_item") for inv in amendments)


def test_in_progress_update_carries_assignee_and_write_root() -> None:
    text = _skill_md("execute")
    updates = [
        inv
        for inv in _invocations(text, "update", "score:work-item")
        if inv["transition"] == "in_progress"
    ]
    assert len(updates) == 1
    assert set(updates[0]["payload"]) == {"assignee", "write_root"}
    flat = _flat(text)
    assert "`orchestra brief <task-slug>`" in flat
    assert "territory and concurrency notes" in flat


def test_verify_work_assesses_only_non_verified() -> None:
    text = _text("verify")
    flat = _flat(text)
    assert "only for a non-verified status" in flat
    assert "Verified status is derived" in flat
    creates = _invocations(text, "create", "conductor:assessment")
    assert creates
    assert all(inv["payload"]["status"] != "verified" for inv in creates)
    assert not [
        inv
        for inv in _invocations(text, "supersede", "conductor:assessment")
        if inv["payload"]["status"] == "verified"
    ]
    assert "Never write an assessment with `status` `verified`." in flat
    assert not _invocations(text, "create", "conductor:release")


def test_phase_position_only_for_notes() -> None:
    plan = _flat(_skill_md("tasks"))
    execute = _flat(_skill_md("execute"))
    assert "only for a note a person must read" in plan
    assert "Phase progress is derived" in _flat(
        (h.REPO_ROOT / "skills/tasks/references/kinds-and-focus.md").read_text()
    )
    assert "Write a phase `score:position` only for a human-readable note" in execute
    assert "Phase progress is derived from work-item states" in execute
    assert not _invocations(_skill_md("tasks"), "create", "score:position")
    assert "Leave the effort position alone until the phase closes" in plan
    phase_end = _flat((h.REPO_ROOT / "skills/verify/references/phase-end.md").read_text())
    assert "effort position narrative" in phase_end


def test_oracle_backed_acceptance_one_create() -> None:
    text = _text("tasks")
    flat = _flat(text)
    assert not [
        inv
        for inv in _invocations(text, "update", "score:acceptance")
        if {"test_ids", "oracle_hashes"} & set(inv["payload"] or {})
    ]
    assert "Never create it and then update it to freeze." in flat
    plan = _skill_md("tasks")
    assert plan.index("8. Oracle author") < plan.index("9. Write the batch")
    shapes = (h.REPO_ROOT / "skills/tasks/references/task-shapes.md").read_text()
    author = (h.REPO_ROOT / "skills/tasks/references/oracle-author.md").read_text()
    creates = _invocations(shapes + "\n" + author, "create", "score:acceptance")
    oracle_backed = [inv for inv in creates if {"test_ids", "oracle_hashes"} <= set(inv["payload"])]
    assert len(oracle_backed) == 1
    assert oracle_backed[0]["payload"]["oracle_hashes"]


def test_plan_phase_batches_through_apply() -> None:
    plan = _skill_md("tasks")
    assert "through one `canon apply` call" in _flat(plan)
    assert "one NDJSON file" in _flat(plan)
    shapes = (h.REPO_ROOT / "skills/tasks/references/task-shapes.md").read_text()
    assert _invocations(shapes, "create", "score:work-item")
    assert "Every `canon create` below shows one line of the plan batch" in _flat(shapes)


def test_verify_work_batches_through_apply() -> None:
    verify = _skill_md("verify")
    assert _apply_count(verify) == 1
    assert "through one `canon apply` call" in _flat(verify)
    lines = _batch_lines(verify)
    assert lines
    assert {line["op"] for line in lines} <= APPLY_OPS
    assert [v for line in lines for v in _line_violations(line)] == []
    last = lines[-1]
    assert (last["op"], last["type"], last["transition"]) == ("update", "score:work-item", "done")
    flat = _flat(verify)
    assert "print each failed entry of `results` and the input line" in flat
    close_batch = _flat((h.REPO_ROOT / "skills/verify/references/close-batch.md").read_text())
    assert "above the final `update` line" in close_batch
    assert "one `canon apply`" in close_batch
