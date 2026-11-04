"""Inventory legacy close evidence and recover attributable records for unfinished work."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

from orchestra.canon.index import RecordIndex
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record, get_list, get_string
from orchestra.conductor.check import RUNNER
from orchestra.tuner.manifest import ManifestError, hash_oracle_files, load_manifest, resolve_commit
from orchestra.tuner.oracle_red import is_assertion_level_red


class RecoveryReport(TypedDict):
    applied: bool
    recoverable: list[str]
    fresh_proof_required: list[str]
    historical: list[str]


def _valid_freeze(payload: JsonObject) -> bool:
    nodes = get_list(payload, "test_ids") or []
    hashes = get_list(payload, "oracle_hashes") or []
    if not nodes or not all(isinstance(node, str) and "::" in node for node in nodes):
        return False
    files: set[str] = set()
    for entry in hashes:
        if not isinstance(entry, str) or not (
            match := re.fullmatch(r"(.+):sha256:[0-9a-f]{64}", entry)
        ):
            return False
        if match[1] in files:
            return False
        files.add(match[1])
    return all(isinstance(node, str) and node.split("::", 1)[0] in files for node in nodes)


def _original_freeze(cwd: Path, acceptance: Record, runs: list[Record]) -> JsonObject | None:
    payload = acceptance["payload"]
    claim_id = get_string(payload, "claim")
    if not claim_id:
        return None
    reds = [
        r
        for r in runs
        if r["payload"].get("criterion_id") == acceptance["id"]
        and r["payload"].get("result") == "fail"
    ]
    if len(reds) != 1:
        return None
    red = reds[0]
    check = red["payload"]
    revision = get_string(check, "revision") or ""
    if (
        not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision)
        or red["recorded_at"] < acceptance["recorded_at"]
        or check.get("runner") != RUNNER
        or check.get("method") != "tdd"
        or check.get("effort") != payload["effort"]
        or check.get("diff_sha256")
        or acceptance["id"] not in (get_list(check, "informed_by") or [])
        or not is_assertion_level_red(red)
    ):
        return None
    try:
        claims = [claim for claim in load_manifest(cwd, revision).claims if claim.id == claim_id]
        if len(claims) != 1:
            return None
        claim = claims[0]
        nodes = get_list(check, "failing_node_ids") or []
        if not nodes or any(node not in claim.tests for node in nodes):
            return None
        frozen: JsonObject = {
            "test_ids": [*claim.tests],
            "oracle_hashes": [
                f"{path}:{digest}" for path, digest in sorted(claim.oracle_hashes.items())
            ],
        }
        if (
            not _valid_freeze(frozen)
            or hash_oracle_files(cwd, revision, list(claim.oracle_hashes)) != claim.oracle_hashes
        ):
            return None
    except (ManifestError, FileNotFoundError):
        return None
    if any(payload.get(field) and payload[field] != value for field, value in frozen.items()):
        return None
    return frozen


def recover_evidence(project: Project, *, apply: bool = False) -> RecoveryReport:
    token = project.change_token()
    index = RecordIndex(project.records())
    report: RecoveryReport = {
        "applied": apply,
        "recoverable": [],
        "fresh_proof_required": [],
        "historical": [],
    }
    ops: list[JsonObject] = []
    tasks = index.of_type("score:work-item")
    runs = [r for r in index.of_type("tuner:check-run") if r["id"] not in index.corrected]
    for acc in index.of_type("score:acceptance"):
        data = acc["payload"]
        if data.get("method") != "tdd" or _valid_freeze(data):
            continue
        phase = index.resolve_subject("score:phase", data.get("phase"))
        if acc["lifecycle_state"] != "active" or (
            phase and phase["lifecycle_state"] in ("done", "withdrawn", "superseded")
        ):
            report["historical"].append(acc["id"])
            continue
        owners = [
            t
            for t in tasks
            if t["lifecycle_state"] != "superseded"
            and t["payload"].get("effort") == data.get("effort")
            and t["payload"].get("phase") == data.get("phase")
            and (acc["subject"] == t["subject"] or acc["subject"].startswith(t["subject"] + "-"))
        ]
        if len(owners) == 1 and owners[0]["lifecycle_state"] in ("done", "withdrawn"):
            report["historical"].append(acc["id"])
            continue
        freeze = (
            _original_freeze(project.project_root, acc, runs)
            if len(owners) == 1 and phase
            else None
        )
        if freeze is None:
            report["fresh_proof_required"].append(acc["id"])
            continue
        ops.append(
            {
                "op": "update",
                "id": acc["id"],
                "type": acc["record_type"],
                "expected_revision": acc["revision"],
                "payload": freeze,
            }
        )
    for run in sorted(runs, key=lambda r: (r["recorded_at"], r["id"])):
        subject = run["subject"]
        if not subject.endswith("-tier2"):
            continue
        phase = index.resolve_subject("score:phase", subject.removesuffix("-tier2"))
        data = run["payload"]
        if data.get("evidence_kind") != "integration" or (
            phase and phase["lifecycle_state"] in ("done", "withdrawn", "superseded")
        ):
            report["historical"].append(run["id"])
            continue
        revision = get_string(data, "revision") or ""
        if not (
            phase
            and phase["payload"].get("effort") == data.get("effort")
            and data.get("method") == "check"
            and data.get("runner") == RUNNER
            and data.get("criterion_id") == subject
            and not data.get("diff_sha256")
            and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision)
        ):
            report["fresh_proof_required"].append(run["id"])
            continue
        try:
            resolve_commit(project.project_root, revision)
        except ManifestError:
            report["fresh_proof_required"].append(run["id"])
            continue
        canonical = phase["subject"] + "-suite"
        if any(r["subject"] == canonical for r in runs):
            report["fresh_proof_required"].append(run["id"])
            continue
        ops.append(
            {
                "op": "correct",
                "id": run["id"],
                "type": run["record_type"],
                "expected_revision": run["revision"],
                "subject": canonical,
                "payload": {"criterion_id": canonical},
            }
        )
    report["recoverable"] = [str(op["id"]) for op in ops]
    if apply and ops:
        project.apply_at_snapshot(ops, token)
    return report
