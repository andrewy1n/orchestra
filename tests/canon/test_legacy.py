import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("canon_legacy", ROOT / "src" / "canon" / "legacy.py")
legacy = importlib.util.module_from_spec(_spec)
sys.modules["canon_legacy"] = legacy
_spec.loader.exec_module(legacy)

FIXTURES = ROOT / "tests" / "fixtures" / "legacy" / "records"

WORK_ITEM_WITH_DEPS = "rec-01a1fc51-76a5-4752-bee0-0474d8ee37dd"
WORK_ITEM_NO_DECISIONS = "rec-404191ec-5110-4b35-ad36-c2f90cdb7e17"
ACCEPTANCE_MULTI = "rec-6f21fdb6-ed88-4965-a020-b9e9b386f343"
CHECK_RUN_MULTI = "rec-0ce05df9-4fec-49fa-80ec-5a82c1d5781d"
CHECK_RUN_INFORMED = "rec-001af826-6491-4f9e-b224-e9be808fe140"
ORACLE_AMENDMENT = "rec-069fe9de-d13b-405a-92c1-ef434a29c14c"
GOAL_WITH_LIST = "rec-39db526b-abbb-4753-b9ff-40b8c05662c2"
REPORT_WITH_ASSIGNMENT_ID = "rec-1752a24e-082e-4699-a67e-ce0fdc469183"
ASSIGNMENT = "rec-0aeb911c-e390-4888-989a-0f1b80378cf6"
FINDING_CONTRADICTED = "rec-1bbc54e9-a6c0-47ea-bc87-561df0a6ec3e"
FINDING_CONTRADICTING = "rec-94362ae8-0f01-4ad1-bfcd-cffa426566b8"
PHASE_BAD_EFFORT = "rec-8152251a-6238-4841-8183-6717775aeb30"
CORRECTED_REPORT = "rec-4f3a0da9-96ab-485e-87ef-586f94afa065"
CHECK_RUN_CORRECTS = "rec-2141a70f-c8a2-4b54-ae34-9dc12cbf02f2"


@pytest.fixture(scope="module")
def old_records():
    return legacy.read_records(FIXTURES)


@pytest.fixture
def by_id(old_records):
    return {r["id"]: r for r in old_records}


def one(old_records, record_id):
    return next(r for r in old_records if r["id"] == record_id)


EXPECTED_TYPE_MAP = {
    "project:active-goal": "plan:effort",
    "project:current-position": "plan:position",
    **{
        f"project:{t}": f"plan:{t}"
        for t in "milestone phase specification design decision constraint work-item acceptance "
        "backlog-item feedback continuity-question".split()
    },
    **{
        f"project:{t}": f"run:{t}"
        for t in "assignment assignment-amendment execution-report integration-report assessment "
        "release proof-packet failed-attempt".split()
    },
    **{
        f"project:{t}": f"aff:{t}"
        for t in "check-run evidence-observation evidence-binding oracle-amendment "
        "investigation-observation finding".split()
    },
}


def synthetic(old_type, payload=None, relationships=None):
    return {
        "id": "rec-00000000-0000-4000-8000-000000000001",
        "record_type": old_type,
        "subject": "s",
        "lifecycle_state": "active",
        "base_kind": "x",
        "identity": {},
        "payload": payload or {},
        "relationships": relationships or {},
        "recorded_at": "2026-01-01T00:00:00Z",
        "revision": "sha256:abc",
        "body": "",
    }


def test_every_old_type_maps_to_its_new_type():
    assert legacy.TYPE_MAP == EXPECTED_TYPE_MAP
    for old_type, new_type in EXPECTED_TYPE_MAP.items():
        assert legacy.transform_record(synthetic(old_type))["record_type"] == new_type


def test_fixtures_cover_every_type_present_in_the_stores(old_records):
    types = {r["record_type"] for r in old_records}
    assert len(types) == 23
    for r in old_records:
        assert legacy.transform_record(r)["record_type"] == EXPECTED_TYPE_MAP[r["record_type"]]


def test_envelope_drops_old_keys_and_keeps_the_rest(old_records):
    for old in old_records:
        new = legacy.transform_record(old)
        for key in ("base_kind", "identity", "stewardship", "epistemic_status"):
            assert key not in new
        for key in ("id", "subject", "lifecycle_state", "recorded_at", "revision", "body"):
            assert new[key] == old[key]
        for key in ("time", "provenance"):
            assert new.get(key) == old.get(key)


def test_transform_does_not_mutate_its_input(old_records):
    snapshot = copy.deepcopy(old_records)
    for old in old_records:
        legacy.transform_record(old)
    assert old_records == snapshot


def test_work_item_splits_decisions_and_requirements(old_records):
    payload = legacy.transform_record(one(old_records, WORK_ITEM_WITH_DEPS))["payload"]
    assert payload["decisions"] == [
        "phase-gate-shape",
        "suite-plugin-defaults",
        "se-workflow-suite-policy",
        "red-first-scope",
        "suite-policy-authority",
    ]
    assert payload["requirements"] == ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]


def test_design_decisions_and_specification_requirements_split(old_records):
    design = next(r for r in old_records if r["record_type"] == "project:design")
    spec = next(r for r in old_records if r["record_type"] == "project:specification")
    assert legacy.transform_record(design)["payload"]["decisions"] == [
        s.strip() for s in design["payload"]["decisions"].split(",") if s.strip()
    ]
    assert isinstance(legacy.transform_record(spec)["payload"]["requirements"], list)


def test_acceptance_splits_test_ids_and_oracle_hashes(old_records):
    old = one(old_records, ACCEPTANCE_MULTI)
    payload = legacy.transform_record(old)["payload"]
    assert payload["test_ids"] == old["payload"]["test_ids"].split(",")
    assert len(payload["test_ids"]) > 1
    assert payload["oracle_hashes"] == old["payload"]["oracle_hashes"].split(",")
    assert len(payload["oracle_hashes"]) == 2


def test_oracle_amendment_hashes_become_lists(old_records):
    payload = legacy.transform_record(one(old_records, ORACLE_AMENDMENT))["payload"]
    assert len(payload["old_hashes"]) == 1 and len(payload["new_hashes"]) == 1


def test_check_run_failing_node_ids_decode_the_json_list(old_records):
    old = one(old_records, CHECK_RUN_MULTI)
    expected = json.loads(old["payload"]["failing_node_ids"])
    assert len(expected) > 1
    assert legacy.transform_record(old)["payload"]["failing_node_ids"] == expected


def test_failing_node_ids_comma_form_splits():
    new = legacy.transform_record(synthetic("project:check-run", {"failing_node_ids": "a::b, c::d"}))
    assert new["payload"]["failing_node_ids"] == ["a::b", "c::d"]


def test_evidence_observation_claim_ids_split():
    new = legacy.transform_record(synthetic("project:evidence-observation", {"claim_ids": "c1,c2"}))
    assert new["payload"]["claim_ids"] == ["c1", "c2"]


def test_empty_string_becomes_empty_list(old_records):
    old = one(old_records, WORK_ITEM_NO_DECISIONS)
    assert old["payload"]["decisions"] == ""
    assert legacy.transform_record(old)["payload"]["decisions"] == []


def test_items_are_stripped_and_empties_dropped():
    new = legacy.transform_record(synthetic("project:work-item", {"requirements": " R1 , ,R2,"}))
    assert new["payload"]["requirements"] == ["R1", "R2"]


def test_existing_list_stays_a_list(old_records):
    old = one(old_records, GOAL_WITH_LIST)
    assert isinstance(old["payload"]["merged_from"], list)
    assert legacy.transform_record(old)["payload"]["merged_from"] == old["payload"]["merged_from"]


def test_effort_merged_from_string_splits():
    new = legacy.transform_record(synthetic("project:active-goal", {"merged_from": "a, b"}))
    assert new["payload"]["merged_from"] == ["a", "b"]


def test_prose_fields_stay_strings():
    payload = {"choice": "a, b", "alternatives": "c, d", "phase": "p", "effort": "e"}
    assert legacy.transform_record(synthetic("project:decision", payload))["payload"] == payload
    pos = {"position": "x, y"}
    assert legacy.transform_record(synthetic("project:current-position", pos))["payload"] == pos


def test_effort_drops_scope(old_records):
    old = one(old_records, GOAL_WITH_LIST)
    assert "scope" in old["payload"]
    assert "scope" not in legacy.transform_record(old)["payload"]


def test_scope_survives_on_other_types():
    new = legacy.transform_record(synthetic("project:current-position", {"scope": "effort"}))
    assert new["payload"]["scope"] == "effort"


def test_supersedes_and_corrects_stay_in_relationships(old_records):
    corrected = legacy.transform_record(one(old_records, CORRECTED_REPORT))
    assert corrected["relationships"] == one(old_records, CORRECTED_REPORT)["relationships"]
    check = legacy.transform_record(one(old_records, CHECK_RUN_CORRECTS))
    assert list(check["relationships"]) == ["corrects"]
    assert "corrects" not in check["payload"]


def test_empty_relationships_are_dropped():
    new = legacy.transform_record(synthetic("project:release", relationships={"supersedes": [], "depends_on": []}))
    assert new["relationships"] == {}
    assert "depends_on" not in new["payload"]


def test_informed_by_moves_to_payload(old_records):
    old = one(old_records, CHECK_RUN_INFORMED)
    new = legacy.transform_record(old)
    assert new["payload"]["informed_by"] == old["relationships"]["informed_by"]
    assert "informed_by" not in new["relationships"]


def test_contradicted_by_moves_to_payload(old_records):
    new = legacy.transform_record(one(old_records, FINDING_CONTRADICTED))
    assert new["payload"]["contradicted_by"] == [FINDING_CONTRADICTING]
    assert new["relationships"] == {}


def test_depends_on_is_left_as_markers_by_the_record_pass(old_records):
    old = one(old_records, WORK_ITEM_WITH_DEPS)
    new = legacy.transform_record(old)
    assert new["payload"]["depends_on"] == [{"$rec": i} for i in old["relationships"]["depends_on"]]
    assert "depends_on" not in new["relationships"]


def test_unknown_type_raises():
    with pytest.raises(legacy.LegacyError, match="unknown old type"):
        legacy.transform_record(synthetic("project:mystery"))


def test_unknown_relationship_raises():
    with pytest.raises(legacy.LegacyError, match="unknown relationship"):
        legacy.transform_record(synthetic("project:release", relationships={"blocks": ["rec-x"]}))


def test_store_resolves_depends_on_ids_to_subjects(old_records, by_id):
    new_records, report = legacy.transform_store(old_records)
    new = next(r for r in new_records if r["id"] == WORK_ITEM_WITH_DEPS)
    expected = []
    for target_id in by_id[WORK_ITEM_WITH_DEPS]["relationships"]["depends_on"]:
        subject = by_id[target_id]["subject"]
        if subject not in expected:
            expected.append(subject)
    assert new["payload"]["depends_on"] == expected
    assert not [u for u in report["unresolved"] if u["record"] == WORK_ITEM_WITH_DEPS and u["field"] == "depends_on"]


def test_store_resolves_execution_report_assignment_id(old_records, by_id):
    new_records, report = legacy.transform_store(old_records)
    new = next(r for r in new_records if r["id"] == REPORT_WITH_ASSIGNMENT_ID)
    assert new["payload"]["assignment"] == by_id[ASSIGNMENT]["subject"]
    assert not [u for u in report["unresolved"] if u["record"] == REPORT_WITH_ASSIGNMENT_ID and u["field"] == "assignment"]


def test_store_reports_unresolved_effort(old_records):
    _, report = legacy.transform_store(old_records)
    hits = [u for u in report["unresolved"] if u["record"] == PHASE_BAD_EFFORT]
    assert hits == [
        {
            "record": PHASE_BAD_EFFORT,
            "record_type": "plan:phase",
            "subject": "evidence-kind",
            "field": "effort",
            "value": "evidence-layer",
        }
    ]


def test_store_reports_missing_depends_on_target_and_assignment(old_records):
    broken_item = synthetic("project:work-item", relationships={"depends_on": ["rec-gone"]})
    broken_report = synthetic("project:execution-report", {"assignment": "rec-missing"})
    broken_report["id"] = "rec-00000000-0000-4000-8000-000000000002"
    _, report = legacy.transform_store([broken_item, broken_report])
    pairs = {(u["field"], u["value"]) for u in report["unresolved"]}
    assert ("depends_on", "rec-gone") in pairs
    assert ("assignment", "rec-missing") in pairs


def test_store_reports_missing_pinned_ids(old_records):
    rec = synthetic("project:check-run", relationships={"informed_by": ["rec-gone"]})
    _, report = legacy.transform_store([rec])
    assert ("informed_by", "rec-gone") in {(u["field"], u["value"]) for u in report["unresolved"]}


def test_store_checks_each_declared_reference_field():
    def rec(n, old_type, subject, payload):
        r = synthetic(old_type, payload)
        r["id"] = f"rec-{n:08d}-0000-4000-8000-000000000000"
        r["subject"] = subject
        return r

    good = [
        rec(1, "project:active-goal", "e", {}),
        rec(2, "project:milestone", "m", {"effort": "e"}),
        rec(3, "project:phase", "p", {"effort": "e", "milestone": "m"}),
        rec(4, "project:decision", "d", {"effort": "e", "phase": "p"}),
        rec(5, "project:work-item", "w", {"effort": "e", "phase": "p", "decisions": "d"}),
        rec(6, "project:acceptance", "a", {"effort": "e", "phase": "p"}),
        rec(7, "project:assignment", "w", {"work_item": "w", "effort": "e"}),
        rec(8, "project:oracle-amendment", "o", {"acceptance": "a", "effort": "e", "phase": "p"}),
    ]
    _, report = legacy.transform_store(good)
    assert report["unresolved"] == []

    bad = copy.deepcopy(good)
    bad[1]["payload"]["effort"] = "no-effort"
    bad[2]["payload"]["milestone"] = "no-milestone"
    bad[3]["payload"]["phase"] = "no-phase"
    bad[4]["payload"]["decisions"] = "d,no-decision"
    bad[6]["payload"]["work_item"] = "no-item"
    bad[7]["payload"]["acceptance"] = "no-acceptance"
    _, report = legacy.transform_store(bad)
    assert {(u["field"], u["value"]) for u in report["unresolved"]} == {
        ("effort", "no-effort"),
        ("milestone", "no-milestone"),
        ("phase", "no-phase"),
        ("decisions", "no-decision"),
        ("work_item", "no-item"),
        ("acceptance", "no-acceptance"),
    }


def test_store_report_counts_per_type(old_records):
    _, report = legacy.transform_store(old_records)
    assert report["total"] == len(old_records)
    assert sum(report["counts"].values()) == len(old_records)
    assert report["counts"]["project:active-goal -> plan:effort"] == sum(
        r["record_type"] == "project:active-goal" for r in old_records
    )


def test_read_records_and_cli_dry_run(tmp_path, capsys):
    copy_dir = tmp_path / "records"
    shutil.copytree(FIXTURES, copy_dir)
    assert len(legacy.read_records(copy_dir)) == sum(1 for _ in copy_dir.glob("*/*.md"))
    assert legacy.main([str(copy_dir), "--dry-run"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["total"] == sum(1 for _ in copy_dir.glob("*/*.md"))
    assert "unresolved" in report


def test_failing_node_ids_empty_string_becomes_empty_list():
    new = legacy.transform_record(synthetic("project:check-run", {"failing_node_ids": ""}))
    assert new["payload"]["failing_node_ids"] == []


def test_payload_subject_equal_to_envelope_subject_is_dropped():
    for old_type in ("project:assignment", "project:execution-report"):
        new = legacy.transform_record(synthetic(old_type, {"subject": "s", "effort": "e"}))
        assert new["payload"] == {"effort": "e"}


def test_payload_subject_differing_from_envelope_subject_raises():
    with pytest.raises(legacy.LegacyError, match="payload.subject"):
        legacy.transform_record(synthetic("project:assignment", {"subject": "other"}))


def test_undeclared_optional_keys_are_kept():
    payload = {"effort": "e", "severity": "high", "revision": "r", "question": "q"}
    assert legacy.transform_record(synthetic("project:finding", payload))["payload"] == payload
