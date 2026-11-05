import hashlib
import json
import subprocess
import sys
from pathlib import Path

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record

NODE = "test_probe.py::test_probe"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _run(root: Path, *, apply: bool = False, expected: int = 0) -> JsonObject:
    args = [sys.executable, "-m", "orchestra.cli", "store", "recover-evidence", "--cwd", str(root)]
    if apply:
        args.append("--apply")
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout)


def _seed(store: Path) -> tuple[Project, Record, Record]:
    project = open_store(store)
    project.create(
        record_type="score:effort", subject="quality", payload={"goal": "quality", "kind": "repair"}
    )
    project.create(
        record_type="score:phase",
        subject="gates",
        payload={"effort": "quality", "ordinal": 1, "title": "Gates"},
        body="## Problem\nCheck\n## Approach\nRepair\n## Exit criteria\nProve",
    )
    task = project.create(
        record_type="score:work-item",
        subject="repair",
        payload={
            "effort": "quality",
            "phase": "gates",
            "kind": "repair",
            "title": "Repair",
            "assignee": "",
        },
        body="## Description\nRepair the gate.",
    )
    acceptance = project.create(
        record_type="score:acceptance",
        subject="repair",
        payload={
            "effort": "quality",
            "phase": "gates",
            "method": "tdd",
            "claim": "probe",
            "verify_command": f"pytest {NODE}",
        },
    )
    return project, task, acceptance


def _red(project: Project, acc: Record) -> tuple[str, str]:
    root = project.project_root
    probe = root / "test_probe.py"
    probe.write_text("def test_probe():\n    assert False\n")
    digest = "sha256:" + hashlib.sha256(probe.read_bytes()).hexdigest()
    (root / ".tuner").mkdir()
    (root / ".tuner" / "manifest.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": "probe",
                        "text": "probe",
                        "tests": [NODE],
                        "oracle_hashes": {probe.name: digest},
                    }
                ]
            }
        )
    )
    (root / "orchestra.toml").write_text(
        (Path(__file__).resolve().parents[2] / "orchestra.toml").read_text()
    )
    _git(root, "add", "test_probe.py", ".tuner/manifest.json", "orchestra.toml")
    _git(root, "commit", "-qm", "freeze probe")
    revision = _git(root, "rev-parse", "HEAD")
    project.create(
        record_type="tuner:check-run",
        subject=acc["subject"],
        payload={
            "criterion_id": acc["id"],
            "informed_by": [acc["id"]],
            "method": "tdd",
            "effort": "quality",
            "revision": revision,
            "result": "fail",
            "runner": "orchestra",
            "signed_by": "",
            "failing_node_ids": [NODE],
        },
        body=f"FAILED {NODE} - AssertionError",
    )
    probe.write_text("def test_probe():\n    pass\n")
    return revision, digest


def _suite(project: Project, revision: str, kind: str) -> Record:
    return project.create(
        record_type="tuner:check-run",
        subject="gates-tier2",
        payload={
            "criterion_id": "gates-tier2",
            "method": "check",
            "effort": "quality",
            "revision": revision,
            "result": "fail",
            "evidence_kind": kind,
            "runner": "orchestra",
            "signed_by": "",
        },
        body="suite log",
    )


def test_completed_history_remains_byte_identical(store: Path) -> None:
    project, task, acc = _seed(store)
    _red(project, acc)
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")
    before = project.records()
    report = _run(store, apply=True)
    assert report["historical"] == [acc["id"]]
    assert project.records() == before


def test_original_freeze_uses_committed_evidence_on_reopened_work(store: Path) -> None:
    project, task, acc = _seed(store)
    _, digest = _red(project, acc)
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")
    project.supersede(task["id"])
    assert _run(store)["recoverable"] == [acc["id"]]
    assert "oracle_hashes" not in project.get(acc["id"])["payload"]
    _run(store, apply=True)
    updated = project.get(acc["id"])["payload"]
    assert updated["oracle_hashes"] == ["test_probe.py:" + digest]
    assert updated["test_ids"] == [NODE]


def test_fresh_proof_required_without_attributable_red(store: Path) -> None:
    project, _, acc = _seed(store)
    old = acc
    acc = project.supersede(acc["id"])["record"]
    _red(project, old)
    before = project.records()
    report = _run(store, apply=True, expected=1)
    assert report["fresh_proof_required"] == [acc["id"]]
    assert report["historical"] == [old["id"]]
    assert project.records() == before


def test_non_suite_evidence_keeps_type_and_subject(store: Path) -> None:
    project, _, acc = _seed(store)
    revision, _ = _red(project, acc)
    run = _suite(project, revision, "other")
    report = _run(store, apply=True)
    assert report["historical"] == [run["id"]]
    assert project.list("tuner:check-run").count(run) == 1
    assert all(r["subject"] != "gates-suite" for r in project.list("tuner:check-run"))


def test_migration_replay(store: Path) -> None:
    project, _, acc = _seed(store)
    revision, _ = _red(project, acc)
    run = _suite(project, revision, "integration")
    before = project.records()
    report = _run(store)
    assert report["recoverable"] == [acc["id"], run["id"]]
    assert project.records() == before
    _run(store, apply=True)
    migrated = project.resolve("tuner:check-run", "gates-suite")
    assert migrated["relationships"]["corrects"] == [run["id"]]
    assert migrated["payload"] == {**run["payload"], "criterion_id": "gates-suite"}
    assert project.get(run["id"]) == run
    after = project.records()
    report = _run(store, apply=True)
    assert report["recoverable"] == []
    assert report["applied"] is False
    assert project.records() == after


def test_idempotent_apply_after_recovery(store: Path) -> None:
    project, _, acc = _seed(store)
    _red(project, acc)
    _run(store, apply=True)
    token = project.change_token()
    _run(store, apply=True)
    assert project.change_token() == token
