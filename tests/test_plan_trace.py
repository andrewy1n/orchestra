"""plan-phase stamps atomic requirement ids and thin acceptances."""

from __future__ import annotations

import json

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import check_skill_text, extract_invocations

SKILL = REPO_ROOT / "skills" / "plan-phase" / "SKILL.md"
EXECUTE_SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"

REQUIRED_WORK_ITEM = {"title", "phase", "kind", "assignee", "effort"}
REQUIRED_ACCEPTANCE = {"method", "phase", "effort", "verify_command", "requirement"}
WRITES = {"create", "update", "supersede", "capture"}
BRIEF_VIEWS = ("brief", "plan", "verification")


def _text() -> str:
    return SKILL.read_text()


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


def _design() -> dict:
    return json.loads((REPO_ROOT / "contract" / "project-design.json").read_text())


def _record(name: str) -> dict:
    return next(record for record in _design()["records"] if record["name"] == name)


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

    design = _design()
    for view_name in BRIEF_VIEWS:
        view = next(v for v in design["views"] if v["name"] == view_name)
        role = next(r for r in view["roles"] if r["name"] == "acceptance")
        assert "criterion" not in role["requires_payload"], view_name


def test_execute_phase_requires_original_text_briefs():
    flat = _flat(EXECUTE_SKILL.read_text())
    assert "Description/Approach" in flat
    assert "quote Description/Approach and requirement texts by id" in flat
    assert "do not paraphrase" in flat or "paraphrase the claim" in flat
    assert (
        "do not invent a claim from criterion" in flat
        or "do not treat empty or legacy `criterion` as the lead claim" in flat
    )
    assert "Do not restate `criterion`" in flat


def test_skill_requires_atomic_ids_and_thin_acceptances():
    flat = _flat(_text())
    assert "atomic" in flat
    assert "thin" in flat
    assert "omit `criterion`" in flat or 'set it to `""`' in flat
    assert "compound" in flat
    assert "When no specification exists, the work-item `## Description` **is** the" in flat
    assert (
        "When no specification exists, omit `requirements`, `decisions`, and `requirement`."
        not in flat
    )
    assert "`incidental` work stays exempt" in flat or "`incidental` may omit" in flat


def test_create_and_capture_examples_match_atomic_thin_shape():
    text = _text()
    work_items = _payloads(text, "project:work-item")
    acceptances = _payloads(text, "project:acceptance")
    assert work_items and acceptances

    covered: set[str] = set()
    for payload in work_items:
        assert REQUIRED_WORK_ITEM <= set(payload)
        assert payload["requirements"]
        for part in (p.strip() for p in payload["requirements"].split(",") if p.strip()):
            covered.add(part)
        assert "ready" not in payload and "wave" not in payload

    for payload in acceptances:
        assert REQUIRED_ACCEPTANCE <= set(payload)
        assert payload["requirement"] in covered
        assert "," not in payload["requirement"]
        criterion = payload.get("criterion", "")
        assert criterion == "" or "criterion" not in payload

    acceptance_subjects = []
    written = set()
    for inv in extract_invocations(text):
        if inv["subcommand"] in WRITES and inv["type"]:
            written.add(inv["type"])
        if inv["type"] == "project:work-item":
            assert all(rel.split(":", 1)[0] == "depends_on" for rel in inv["rels"])
        for part in inv["records"] or []:
            if inv["subcommand"] != "capture":
                continue
            written.add(part.get("type"))
            if part.get("type") == "project:acceptance":
                acceptance_subjects.append(part["subject"])
                assert "criterion" not in part["payload"] or part["payload"].get("criterion") == ""
    assert "project:assessment" not in written
    assert "project:integration-report" not in written
    assert "<task-slug>" in acceptance_subjects
    assert "<task-slug>-perf" in acceptance_subjects


def test_plan_phase_trace_invocations_are_contract_legal(resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    bundles = {bundle["id"]: bundle for bundle in resolved_contract.get("bundles", [])}
    violations = check_skill_text(_text(), defs, bundles)
    assert not violations, "\n".join(violations)


def test_plan_phase_oracle_author_and_freeze():
    flat = _flat(_text())
    assert "oracle-author" in flat
    assert "assertion-level" in flat
    assert "test_ids" in flat
    assert "oracle_hashes" in flat
    assert "freeze" in flat
    assert "requirement / specification text only" in flat or "requirement/spec text" in flat
    # Freeze update example is contract-shaped.
    freeze_payloads = [
        p
        for p in _payloads(_text(), "project:acceptance")
        if p.get("test_ids") and p.get("oracle_hashes")
    ]
    assert freeze_payloads
    for payload in freeze_payloads:
        assert "sha256:" in payload["oracle_hashes"]
        assert payload.get("method") == "tdd"
        assert payload.get("requirement")
        assert "pytest" in payload.get("verify_command", "")


def test_execute_phase_oracle_amendment_and_frozen_oracle(resolved_contract):
    text = EXECUTE_SKILL.read_text()
    flat = _flat(text)
    assert "oracle-amendment" in flat
    assert "frozen oracle" in flat
    assert "oracle_hashes" in flat
    assert "status" in flat and "requested" in flat and "approved" in flat
    defs = h.record_defs_by_id(resolved_contract)
    bundles = {bundle["id"]: bundle for bundle in resolved_contract.get("bundles", [])}
    violations = check_skill_text(text, defs, bundles)
    assert not violations, "\n".join(violations)
    creates = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "project:oracle-amendment"
    ]
    assert creates and creates[0]["payload"]
    payload = creates[0]["payload"]
    assert payload["status"] == "requested"
    assert {"acceptance", "effort", "phase", "old_hashes", "new_hashes", "status"} <= set(
        payload
    )


def test_verify_work_mechanical_oracle_backed():
    verify = (REPO_ROOT / "skills" / "verify-work" / "SKILL.md").read_text()
    flat = _flat(verify)
    assert "mechanical" in flat
    assert "assertion-level" in flat
    assert "oracle-backed" in flat
    assert "oracle_hashes" in flat or "oracle-amendment" in flat


def test_thin_deliver_cli_capture(store, cli, resolved_contract):
    """Thin deliver acceptance (no criterion prose) via real create + capture."""
    defs = h.record_defs_by_id(resolved_contract)
    phase = "thin-deliver-phase"
    effort = "thin-deliver-effort"
    h.create_generic_record(
        cli,
        defs,
        "project:phase",
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
        "project:acceptance",
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
            "type": "project:work-item",
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
                "requirements": "R1",
            },
            "body": "## Description\n\nR1: thin acceptance works through CLI capture.\n",
        },
        {
            "type": "project:acceptance",
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
    captured = cli(
        "capture",
        "--bundle",
        "project:specified-work",
        "--records",
        json.dumps(records),
    )
    assert captured.returncode == 0, captured.stdout + captured.stderr
    listed = cli("list", "--type", "project:acceptance", "--subject", "thin-deliver-capture", "--full")
    assert listed.returncode == 0, listed.stdout + listed.stderr
    accs = json.loads(listed.stdout)["records"]
    assert len(accs) == 1
    assert accs[0]["payload"]["requirement"] == "R1"
    assert not accs[0]["payload"].get("criterion")
