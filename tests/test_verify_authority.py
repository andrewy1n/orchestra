"""Fail closed if verify-work or close_batch invent binary check-runs for tdd/check.

R5 / check-run-authority: tdd/check check-runs come only from
`aff check` (or an already runner-produced id). Agents write
assessments, not invented pass/fail.
"""

from __future__ import annotations

import re
import sys

import pytest

from conftest import REPO_ROOT
from skill_extraction import extract_invocations
from affidavit import close_batch

SKILL = REPO_ROOT / "skills" / "verify-work" / "SKILL.md"
SCRIPT = REPO_ROOT / "affidavit" / "close_batch.py"


def _skill() -> str:
    return SKILL.read_text()


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_skill_documents_affidavit_check_for_tdd_and_check():
    text = _skill()
    flat = _normalized(text)
    assert "aff check" in text
    assert "--acceptance" in text
    assert "Do **not** `adaptive-artifacts create --type" in text
    assert "project:check-run` for `method` `tdd` or `check`" in flat or (
        "for `method` `tdd` or `check`" in text
    )
    assert "assessment" in flat


def test_skill_does_not_document_hand_create_for_tdd_or_check_methods():
    creates = [
        inv
        for inv in extract_invocations(_skill())
        if inv["subcommand"] == "create"
        and inv["type"] == "project:check-run"
        and inv.get("payload")
    ]
    assert creates, "manual check-run create examples must remain"
    for inv in creates:
        method = inv["payload"].get("method")
        assert method == "manual", (
            f"verify-work must not document create with method={method!r}; "
            "tdd/check check-runs come from aff check"
        )


def test_skill_keeps_assessment_writes():
    assessments = [
        inv
        for inv in extract_invocations(_skill())
        if inv["subcommand"] in {"create", "supersede"}
        and inv["type"] == "project:assessment"
        and inv.get("payload")
    ]
    assert assessments
    assert "next" in assessments[0]["payload"]


def test_skill_close_request_references_check_run_id_for_runner_methods():
    text = _skill()
    assert "check_run_id" in text
    assert '"method": "tdd"' in text or '"method": "tdd"' in text.replace(" ", "")
    # Close examples for tdd/check must not invent revision/signed_by creates.
    close_at = text.index("## Close")
    close = text[close_at:]
    assert "check_run_id" in close
    assert '"method": "tdd"' in close
    assert '"method": "check"' in close
    # Runner close-request entries may carry revision (ancestry) with check_run_id.
    # Invented shape is method+revision without a runner check_run_id.
    for method in ("tdd", "check"):
        for block in re.findall(
            rf'\{{[^{{}}]*"method"\s*:\s*"{method}"[^{{}}]*\}}',
            close,
        ):
            if '"revision"' in block:
                assert '"check_run_id"' in block, block


def test_close_batch_refuses_invented_tdd_pass_without_check_run_id():
    request = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": None,
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "result": "pass",
                "method": "tdd",
                "revision": "abc123",
                "signed_by": "",
            }
        ],
        "finding": None,
    }
    with pytest.raises(close_batch.CloseRequestError, match="check_run_id"):
        close_batch.build_batch(request)


def test_close_batch_refuses_invented_check_fail_without_check_run_id():
    request = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": None,
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "result": "fail",
                "method": "check",
                "revision": "abc123",
                "signed_by": "",
            }
        ],
        "finding": {
            "claim": "gap",
            "basis": "deferred",
            "invalidated_when": "re-run",
            "body": "## Evidence\n\nx\n\n## Consequence\n\ny\n\n## Follow-up\n\nz",
        },
    }
    with pytest.raises(close_batch.CloseRequestError, match="check_run_id"):
        close_batch.build_batch(request)


def test_close_batch_does_not_emit_check_run_create_for_runner_methods():
    request = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": "rec-er",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "method": "tdd",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
                "revision": "abc123",
                "red_check_run_id": "rec-red-cr",
                "red_result": "fail",
                "red_revision": "dirty",
                "red_runner": "aff",
                "red_diff_sha256": "c" * 64,
            }
        ],
        "finding": None,
    }

    def loader(cid: str) -> dict:
        entry = request["criteria"][0]
        if cid == entry["check_run_id"]:
            return {
                "id": cid,
                "payload": {
                    "criterion_id": entry["criterion_id"],
                    "result": entry["result"],
                    "runner": "aff",
                    "revision": entry["revision"],
                    "method": "tdd",
                },
            }
        if cid == entry["red_check_run_id"]:
            return {
                "id": cid,
                "payload": {
                    "criterion_id": entry["criterion_id"],
                    "result": entry["red_result"],
                    "runner": entry["red_runner"],
                    "revision": entry["red_revision"],
                    "diff_sha256": entry["red_diff_sha256"],
                    "method": "tdd",
                },
            }
        raise LookupError(cid)

    ops = close_batch.build_batch(request, load_check_run=loader)
    assert [op["op"] for op in ops] == ["update"]
    assert not any(op.get("type") == "project:check-run" for op in ops)


def test_close_batch_still_creates_manual_check_runs():
    ops = close_batch.build_batch(
        {
            "subject": "task-1",
            "effort": "effort-1",
            "work_item_id": "rec-wi",
            "transition": "done",
            "execution_report_id": "rec-er",
            "acceptance_ids": ["rec-ac1"],
            "criteria": [
                {
                    "criterion_id": "rec-ac1",
                    "method": "manual",
                    "result": "pass",
                    "revision": "abc123",
                    "signed_by": "maintainer",
                }
            ],
            "finding": None,
        }
    )
    assert ops[0]["type"] == "project:check-run"
    assert ops[0]["payload"]["method"] == "manual"
    assert ops[0]["payload"]["result"] == "pass"


def test_close_batch_source_mentions_runner_authority():
    src = SCRIPT.read_text()
    assert "aff check" in src or "runner-produced" in src
    assert "check_run_id" in src
    assert "RUNNER_METHODS" in src
