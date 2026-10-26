"""Schema module self-consistency checks.

Every check derives from the plan, run, and aff schema modules, so none
hardcode record type names or counts.
"""

from __future__ import annotations

import json

import pytest

import helpers as h
from conftest import CANON_ROOT, make_git_repo, run_cli

_DEFS = h.schema_defs()
_RECORD_IDS = sorted(_DEFS)


def _edge_cases():
    return [
        (record_id, src, dest)
        for record_id, record_def in _DEFS.items()
        for src, dest in h.all_edges(record_def)
    ]


def _ref_cases():
    cases = []
    for record_id, record_def in _DEFS.items():
        for field, form in record_def["required"].items():
            if "ref" in form or ("list" in form and "ref" in form["list"]):
                cases.append((record_id, field))
    return cases


def test_namespaces_cover_plan_run_aff():
    assert {rid.split(":", 1)[0] for rid in _RECORD_IDS} == {"plan", "run", "aff"}


@pytest.mark.parametrize("record_id", _RECORD_IDS)
def test_record_type_creates_and_reads_back(cli, record_id):
    record = h.create_generic_record(cli, _DEFS, record_id)
    assert record["record_type"] == record_id
    assert record["lifecycle_state"] == _DEFS[record_id]["lifecycle"]["initial"]

    readback = cli("get", "--type", record_id, "--id", record["id"])
    assert readback.returncode == 0, readback.stdout + readback.stderr
    stored = json.loads(readback.stdout)
    assert stored["id"] == record["id"]
    assert stored["subject"] == record["subject"]
    assert stored["lifecycle_state"] == record["lifecycle_state"]


@pytest.mark.parametrize("record_id", _RECORD_IDS)
def test_store_validates_after_creating_a_record(cli, record_id):
    h.create_generic_record(cli, _DEFS, record_id)
    result = cli("validate")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout).get("status") == "valid"


@pytest.mark.parametrize("record_id,src,dest", _edge_cases(), ids=lambda v: str(v))
def test_lifecycle_transition_is_exercisable(cli, record_id, src, dest):
    record_def = _DEFS[record_id]
    record = h.drive_to_state(cli, _DEFS, record_id, src)
    reached = h._apply_transition(cli, record_def, record_id, record, dest)
    assert reached["lifecycle_state"] == dest


@pytest.mark.parametrize("record_id,field", _ref_cases(), ids=lambda v: str(v))
def test_reference_to_a_missing_record_is_refused(cli, record_id, field):
    form = _DEFS[record_id]["required"][field]
    if "list" in form:
        missing = ["does-not-exist-anywhere"]
    else:
        missing = "does-not-exist-anywhere"
    payload = {}
    cache: dict = {}
    for name, other in _DEFS[record_id]["required"].items():
        payload[name] = h._generic_value(cli, _DEFS, name, other, cache)
    payload[field] = missing
    args = ["create", "--type", record_id, "--subject", "bad-ref", "--payload", json.dumps(payload)]
    body = h.generic_body(_DEFS[record_id])
    if body:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode != 0, result.stdout
    assert "does-not-exist-anywhere" in result.stdout + result.stderr


@pytest.mark.parametrize("record_id,field", _ref_cases(), ids=lambda v: str(v))
def test_reference_to_a_real_record_is_accepted(cli, record_id, field):
    record = h.create_generic_record(cli, _DEFS, record_id)
    assert record["payload"][field] is not None
    assert json.loads(cli("validate").stdout).get("status") == "valid"


_APPROVAL_OPTIONAL_NOTES = (
    ("plan:continuity-question", "answer"),
    ("aff:check-run", "signed_note"),
    ("aff:finding", "resolution_note"),
)


@pytest.mark.parametrize("record_id,field", _APPROVAL_OPTIONAL_NOTES, ids=lambda v: str(v))
def test_approval_optional_payload_note_fields_are_optional(record_id, field):
    form = _DEFS[record_id]["fields"][field]
    assert form.get("optional") is True


@pytest.mark.parametrize("record_id,field", _APPROVAL_OPTIONAL_NOTES, ids=lambda v: str(v))
def test_approval_optional_payload_note_fields_accepted(cli, record_id, field):
    note = f"approval-{field}-note"
    record = h.create_generic_record(cli, _DEFS, record_id, extra_payload={field: note})
    assert record["payload"].get(field) == note
    stored = json.loads(cli("get", "--type", record_id, "--id", record["id"]).stdout)
    assert stored["payload"].get(field) == note


def test_effort_has_no_scope_and_position_keeps_it():
    assert "scope" not in _DEFS["plan:effort"]["fields"]
    assert "scope" in _DEFS["plan:position"]["fields"]


def test_staged_types_take_depends_on_subjects(cli):
    first = h.create_generic_record(cli, _DEFS, "plan:work-item")
    second = h.create_generic_record(
        cli, _DEFS, "plan:work-item", extra_payload={"depends_on": [first["subject"]]}
    )
    assert second["payload"]["depends_on"] == [first["subject"]]


def test_phase_gate_defaults_to_mode_none(tmp_path):
    from orchestra import suite

    repo = make_git_repo()
    assert run_cli("init", "--schemas", "plan,run,aff", root=repo).returncode == 0
    policy = suite.load_suite_policy(repo)
    assert policy.mode == "none"
    assert policy.gate == "required"


def test_phase_gate_reads_store_config():
    from orchestra import suite

    repo = make_git_repo()
    assert run_cli("init", "--schemas", "plan,run,aff", root=repo).returncode == 0
    config_path = repo / ".artifacts" / "config.json"
    config = json.loads(config_path.read_text())
    config["settings"] = {
        "run": {"phase_gate": {"suite": {"mode": "full", "command": "pytest -q", "gate": "advisory"}}}
    }
    config_path.write_text(json.dumps(config))
    policy = suite.load_suite_policy(repo)
    assert (policy.mode, policy.command, policy.gate) == ("full", "pytest -q", "advisory")
