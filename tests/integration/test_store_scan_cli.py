from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record

EFFORT = "ef"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
PHASE_PAYLOAD: JsonObject = {"title": "Ph", "ordinal": 1, "effort": EFFORT}


def _orchestra(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *argv],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _store(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", "ph", PHASE_PAYLOAD)
    return project


def _phase(project: Project) -> Record:
    return project.resolve("score:phase", "ph")


def _landing(project: Project, slug: str = "ph") -> Record:
    payload: JsonObject = {
        "phase": slug,
        "number": 7,
        "url": "https://github.com/o/r/pull/7",
        "head_sha": HEAD,
        "result": "success",
    }
    return create(project, "conductor:landing", slug, payload)


def _packet(project: Project, slug: str = "ph") -> Record:
    payload: JsonObject = {
        "phase": slug,
        "effort": EFFORT,
        "revision": HEAD,
        "base": "main",
        "kind": "claims",
    }
    return create(project, "conductor:proof-packet", slug, payload)


def _acceptance(project: Project, subject: str = "acc") -> Record:
    payload: JsonObject = {
        "method": "tdd",
        "effort": EFFORT,
        "verify_command": "uv run pytest -q",
        "requirement": "R1",
    }
    return create(project, "score:acceptance", subject, payload)


def _check_run(project: Project, subject: str = "acc") -> Record:
    payload: JsonObject = {
        "criterion_id": subject,
        "revision": HEAD,
        "result": "pass",
        "effort": EFFORT,
        "method": "tdd",
        "signed_by": "",
    }
    return create(project, "tuner:check-run", subject, payload)


def _finding(project: Project, subject: str = "fnd") -> Record:
    payload: JsonObject = {
        "claim": "c",
        "basis": "b",
        "invalidated_when": "i",
        "effort": EFFORT,
        "needs": "n",
    }
    return create(project, "tuner:finding", subject, payload)


def _binding(project: Project, subject: str = "bnd") -> Record:
    payload: JsonObject = {
        "observation_id": "obs",
        "claim_id": "claim",
        "base_rev": "base",
        "head_rev": "head",
    }
    return create(project, "tuner:evidence-binding", subject, payload)


def _specification(project: Project, requirements: str) -> Record:
    sections = ["Acceptance criteria", "Constraints", "Non-goals", "Invariants", "Assumptions"]
    body = "\n\n".join(
        [f"## Requirements\n\n{requirements}"] + [f"## {s}\n\nText." for s in sections]
    )
    payload: JsonObject = {
        "weight": "full",
        "phase": "ph",
        "effort": EFFORT,
        "requirements": ["R1"],
    }
    return create(project, "score:specification", "ph", payload, body=body)


def _malform(project: Project, record: Record, **fields: JsonValue) -> Record:
    store, _ = project._session()
    payload = {key: value for key, value in record["payload"].items() if key not in fields}
    payload.update({key: value for key, value in fields.items() if value is not None})
    changed = Record(**record)
    changed["payload"] = payload
    return store.write_record(changed, expected_revision=record["revision"])


def _snapshot(project: Project) -> tuple[list[tuple[str, str]], str]:
    records = sorted((record["id"], record["revision"]) for record in project.records())
    return records, project.change_token()


def _findings(result: subprocess.CompletedProcess[str]) -> list[JsonObject]:
    return [json.loads(line) for line in result.stdout.splitlines()]


def test_r14_scan_reports_each_rejected_record_with_its_id_and_field(tmp_path: Path) -> None:
    project = _store(tmp_path)
    phase = _malform(project, _phase(project), ordinal="1")
    landing = _malform(project, _landing(project), number="7")
    packet = _malform(project, _packet(project), kind=None)

    result = _orchestra(tmp_path, "store", "scan", "--json")

    found = {
        (entry["record_id"], entry["record_type"], entry["field"]) for entry in _findings(result)
    }
    assert found == {
        (phase["id"], "score:phase", "ordinal"),
        (landing["id"], "conductor:landing", "number"),
        (packet["id"], "conductor:proof-packet", "kind"),
    }
    assert all(entry["message"] for entry in _findings(result))


def test_r14_scan_prints_one_line_per_finding_with_record_id_and_field(tmp_path: Path) -> None:
    project = _store(tmp_path)
    landing = _malform(project, _landing(project), result="merged")

    result = _orchestra(tmp_path, "store", "scan")

    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert landing["id"] in lines[0]
    assert "result" in lines[0]


def test_r14_scan_skips_records_that_are_not_live(tmp_path: Path) -> None:
    project = _store(tmp_path)
    old_phase = _malform(project, _phase(project), ordinal="1")
    project.supersede(old_phase["id"], payload=PHASE_PAYLOAD)
    old_landing = _malform(project, _landing(project), number="7")
    project.correct(
        old_landing["id"],
        payload={
            "phase": "ph",
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": HEAD,
            "result": "success",
        },
    )

    result = _orchestra(tmp_path, "store", "scan", "--json")

    assert result.stdout == ""


def test_r15_scan_exits_zero_when_every_record_is_accepted(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _landing(project)
    _packet(project)

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_r15_scan_exits_zero_on_a_store_with_no_phase_records(tmp_path: Path) -> None:
    make_project(tmp_path)

    result = _orchestra(tmp_path, "store", "scan", "--json")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_r16_scan_exits_one_when_a_record_is_rejected(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _malform(project, _phase(project), title=None)

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 1
    assert result.stdout.strip()


def test_r16_scan_exits_one_with_json_output(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _malform(project, _packet(project), revision=None)

    result = _orchestra(tmp_path, "store", "scan", "--json")

    assert result.returncode == 1
    assert [entry["field"] for entry in _findings(result)] == ["revision"]


def test_scan_exits_two_when_the_store_cannot_be_opened(tmp_path: Path) -> None:
    result = _orchestra(tmp_path, "store", "scan", "--cwd", str(tmp_path / "missing"))

    assert result.returncode == 2
    assert result.stderr.strip()


def test_r17_scan_leaves_the_store_unchanged(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _malform(project, _phase(project), ordinal="1")
    _malform(project, _landing(project), number="7")
    before = _snapshot(project)

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 1
    assert _snapshot(project) == before


def _reported(tmp_path: Path) -> set[tuple[JsonValue, JsonValue, JsonValue]]:
    result = _orchestra(tmp_path, "store", "scan", "--json")
    return {
        (entry["record_id"], entry["record_type"], entry["field"]) for entry in _findings(result)
    }


def test_r15_evidence_scan_reports_a_malformed_check_run_with_id_and_field(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    check_run = _malform(project, _check_run(project), result="maybe")

    assert _reported(tmp_path) == {(check_run["id"], "tuner:check-run", "result")}


def test_r15_evidence_scan_reports_a_malformed_acceptance_with_id_and_field(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    acceptance = _malform(project, _acceptance(project), method="sometimes")

    assert _reported(tmp_path) == {(acceptance["id"], "score:acceptance", "method")}


def test_r15_evidence_scan_reports_a_malformed_finding_and_evidence_binding(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    finding = _malform(project, _finding(project), needs=None)
    binding = _malform(project, _binding(project), head_rev=None)

    assert _reported(tmp_path) == {
        (finding["id"], "tuner:finding", "needs"),
        (binding["id"], "tuner:evidence-binding", "head_rev"),
    }


def test_r15_evidence_scan_reports_a_specification_with_a_malformed_requirement_list(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    specification = _specification(project, "R1: first\nR1: again")

    assert _reported(tmp_path) == {(specification["id"], "score:specification", "body")}


def test_r15_evidence_scan_reports_a_light_phase_with_a_malformed_requirement_list(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    project.supersede(
        _phase(project)["id"],
        payload={**PHASE_PAYLOAD, "weight": "light"},
        body=(
            "## Problem\n\nText.\n\n## Approach\n\nText.\n\n## Exit criteria\n\nText.\n\n"
            "## Requirements\n\nR1: first\nR1: again\n"
        ),
    )

    assert _reported(tmp_path) == {(_phase(project)["id"], "score:phase", "body")}


def test_r15_evidence_scan_accepts_well_formed_evidence_records(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _acceptance(project)
    _check_run(project)
    _finding(project)
    _binding(project)
    _specification(project, "R1: first")

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_r15_evidence_scan_skips_corrected_and_superseded_evidence_records(
    tmp_path: Path,
) -> None:
    project = _store(tmp_path)
    check_run = _malform(project, _check_run(project), result="maybe")
    project.correct(check_run["id"], payload=dict(_check_run(project, "other")["payload"]))
    acceptance = _malform(project, _acceptance(project), method="sometimes")
    project.supersede(acceptance["id"], payload=dict(_acceptance(project, "other")["payload"]))

    assert _reported(tmp_path) == set()


def test_r15_evidence_scan_leaves_the_store_unchanged(tmp_path: Path) -> None:
    project = _store(tmp_path)
    _malform(project, _check_run(project), result="maybe")
    _malform(project, _acceptance(project), method="sometimes")
    before = _snapshot(project)

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 1
    assert _snapshot(project) == before
