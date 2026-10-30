"""plan-phase stamps atomic requirement ids and thin acceptances."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import helpers as h
from skill_extraction import check_skill_text, extract_invocations

REQUIRED_WORK_ITEM = {"title", "phase", "kind", "assignee", "effort"}
REQUIRED_ACCEPTANCE = {"method", "phase", "effort", "verify_command", "requirement"}
WRITES = {"create", "update", "supersede", "capture"}


def _text() -> str:
    return h.skill_text("plan-phase")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _payloads(text: str, record_type: str) -> list[dict]:
    payloads = []
    for inv in extract_invocations(text):
        if inv["type"] == record_type and inv["payload"]:
            payloads.append(inv["payload"])
        for part in inv["records"] or []:
            if part.get("type") == record_type:
                payloads.append(part["payload"])
    return payloads


def _record(name: str) -> dict:
    return h.record_def(name)


def test_trace_fields_are_optional_in_the_contract():
    work_item = _record("work-item")
    acceptance = _record("acceptance")
    assert {"requirements", "decisions"} <= set(work_item["optional_payload"])
    assert "requirement" in acceptance["optional_payload"]
    work_required = set(work_item["payload"]) - set(work_item["optional_payload"])
    acceptance_required = set(acceptance["payload"]) - set(acceptance["optional_payload"])
    assert "requirements" not in work_required
    assert "decisions" not in work_required
    assert "requirement" not in acceptance_required


def test_criterion_optional_in_contract():
    acceptance = _record("acceptance")
    assert "criterion" in acceptance["payload"]
    assert "criterion" in acceptance["optional_payload"]
    required = set(acceptance["payload"]) - set(acceptance["optional_payload"])
    assert "criterion" not in required


def test_execute_phase_requires_original_text_briefs():
    flat = _flat(h.skill_text("execute-phase"))
    assert "quotes (verbatim, by id) work-item Description/Approach, linked requirement text" in flat
    assert "Do not paraphrase claims or treat empty/legacy `criterion` as the lead claim." in flat
    assert "Do not restate `criterion`" in flat


def test_skill_requires_atomic_ids_and_thin_acceptances():
    flat = _flat(_text())
    assert "atomic requirement ids in `requirements` (JSON array of atomic ids; never compound)" in flat
    assert "New acceptances are **thin**: omit `criterion` or `\"\"`." in flat
    assert "else id'd list in `## Description`" in flat
    assert "`incidental` may omit" in flat


def test_create_examples_match_atomic_thin_shape():
    text = _text()
    creates = [inv for inv in extract_invocations(text) if inv["subcommand"] == "create" and inv["payload"]]
    work_items = [inv["payload"] for inv in creates if inv["type"] == "score:work-item"]
    acceptances = [inv for inv in creates if inv["type"] == "score:acceptance"]
    assert work_items and acceptances

    covered: set[str] = set()
    for payload in work_items:
        assert REQUIRED_WORK_ITEM <= set(payload)
        assert payload["requirements"]
        covered.update(payload["requirements"])
        assert "ready" not in payload and "wave" not in payload

    for inv in acceptances:
        payload = inv["payload"]
        assert REQUIRED_ACCEPTANCE <= set(payload)
        assert payload["requirement"] in covered
        assert "," not in payload["requirement"]
        assert payload.get("criterion", "") == ""

    written = {inv["type"] for inv in extract_invocations(text) if inv["subcommand"] in WRITES}
    assert "conductor:assessment" not in written
    assert "conductor:integration-report" not in written
    subjects = {re.search(r'--subject "([^"]+)"', inv["raw"]).group(1) for inv in acceptances}
    assert {"<task-slug>", "<task-slug>-perf"} <= subjects


def test_plan_phase_trace_invocations_are_contract_legal(resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    violations = check_skill_text(_text(), defs)
    assert not violations, "\n".join(violations)


def test_plan_phase_oracle_author_and_freeze():
    flat = _flat(_text())
    assert "oracle-author" in flat
    assert "assertion-level" in flat
    assert "test_ids" in flat
    assert "oracle_hashes" in flat
    assert "freeze" in flat
    assert "Give it only original requirement / specification text" in flat
    # Freeze update example is contract-shaped.
    freeze_payloads = [
        p
        for p in _payloads(_text(), "score:acceptance")
        if p.get("test_ids") and p.get("oracle_hashes")
    ]
    assert freeze_payloads
    for payload in freeze_payloads:
        assert all(":sha256:" in entry for entry in payload["oracle_hashes"])
        assert payload.get("method") == "tdd"
        assert payload.get("requirement")
        assert "pytest" in payload.get("verify_command", "")


def test_execute_phase_oracle_amendment_and_frozen_oracle(resolved_contract):
    text = h.skill_text("execute-phase")
    flat = _flat(text)
    assert "### Frozen oracle (do not edit)" in text
    assert "oracle_hashes" in flat
    assert "Parent adds a signed amendment in `.tuner/manifest.json`" in flat
    defs = h.record_defs_by_id(resolved_contract)
    violations = check_skill_text(text, defs)
    assert not violations, "\n".join(violations)
    assert not [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] in {"create", "supersede"} and inv["type"] == "tuner:oracle-amendment"
    ]


def test_verify_work_mechanical_oracle_backed():
    verify = h.skill_text("verify-work")
    flat = _flat(verify)
    assert "mechanical" in flat
    assert "assertion-level" in flat
    assert "oracle-backed" in flat
    assert "oracle_hashes" in flat or "oracle-amendment" in flat


def test_thin_deliver_cli_capture(store, cli, resolved_contract):
    """Thin deliver acceptance (no criterion prose) via real create + apply."""
    defs = h.record_defs_by_id(resolved_contract)
    phase = "thin-deliver-phase"
    effort = "thin-deliver-effort"
    h.create_generic_record(
        cli,
        defs,
        "score:phase",
        subject=phase,
        extra_payload={"title": "Thin deliver phase", "ordinal": 1, "effort": effort},
    )

    create_payload = {
        "method": "tdd",
        "phase": phase,
        "effort": effort,
        "verify_command": "true",
        "requirement": "R1",
    }
    created = cli(
        "create",
        "--type",
        "score:acceptance",
        "--subject",
        "thin-deliver-create",
        "--payload",
        json.dumps(create_payload),
    )
    assert created.returncode == 0, created.stdout + created.stderr
    create_rec = json.loads(created.stdout)["record"]
    assert create_rec["payload"].get("requirement") == "R1"
    assert not create_rec["payload"].get("criterion")

    records = [
        {
            "type": "score:work-item",
            "subject": "thin-deliver-capture",
            "payload": {
                "title": "Thin capture task",
                "phase": phase,
                "kind": "deliver",
                "assignee": "",
                "effort": effort,
                "executor": "inline",
                "size": "S",
                "estimate_minutes": 5,
                "requirements": ["R1"],
            },
            "body": "## Description\n\nR1: thin acceptance works through CLI capture.\n",
        },
        {
            "type": "score:acceptance",
            "subject": "thin-deliver-capture",
            "payload": {
                "method": "check",
                "phase": phase,
                "effort": effort,
                "verify_command": "true",
                "requirement": "R1",
            },
        },
    ]
    batch = Path(tempfile.mkdtemp(prefix="plan-trace-")) / "batch.ndjson"
    batch.write_text(
        "\n".join(json.dumps({"op": "create", **record}) for record in records) + "\n",
        encoding="utf-8",
    )
    captured = cli("apply", str(batch))
    assert captured.returncode == 0, captured.stdout + captured.stderr
    listed = cli("list", "--type", "score:acceptance", "--subject", "thin-deliver-capture", "--full")
    assert listed.returncode == 0, listed.stdout + listed.stderr
    accs = json.loads(listed.stdout)["records"]
    assert len(accs) == 1
    assert accs[0]["payload"]["requirement"] == "R1"
    assert not accs[0]["payload"].get("criterion")
