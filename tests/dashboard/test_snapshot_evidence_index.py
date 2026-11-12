from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import make_project

from dashboard.backend import phase as phase_mod
from dashboard.backend.snapshot import load_snapshot
from orchestra import derive
from orchestra.canon import record as record_mod
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.derive import RequirementStatus


def _create(
    project: Project,
    record_type: str,
    subject: str,
    payload: JsonObject,
    body: str | None = None,
) -> Record:
    if body is None:
        body = "\n\n".join(
            f"## {name}\n\nText." for name in project.schemas().types[record_type].sections
        )
    return project.create(record_type=record_type, subject=subject, payload=payload, body=body)


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    moment = datetime(2026, 11, 1, tzinfo=timezone.utc)

    def now() -> str:
        nonlocal moment
        moment += timedelta(seconds=1)
        return moment.isoformat()

    monkeypatch.setattr(record_mod, "now", now)
    project = make_project(tmp_path)
    _create(project, "score:effort", "e", {"goal": "Ship", "kind": "deliver"})
    for ordinal, name in enumerate(("finished", "current"), 1):
        phase = _create(
            project,
            "score:phase",
            name,
            {"title": name, "ordinal": ordinal, "effort": "e", "weight": "light"},
            "## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
            "## Requirements\n\nR1: First.\nR2: Second.\n",
        )
        phase = project.update(phase["id"], transition="in_progress")
        if name == "finished":
            project.update(phase["id"], transition="done")
        for requirement in ("R1", "R2"):
            fields: JsonObject = (
                {"requirement": requirement}
                if requirement == "R1"
                else {"requirements": [requirement]}
            )
            acceptance = _create(
                project,
                "score:acceptance",
                f"{name}-{requirement}",
                {
                    "method": "check",
                    "phase": name,
                    "effort": "e",
                    "verify_command": "true",
                    **fields,
                },
            )
            for result in ("fail", "pass") if name == "finished" else ("fail",):
                _create(
                    project,
                    "tuner:check-run",
                    f"{name}-{requirement}-{result}",
                    {
                        "criterion_id": acceptance["id"],
                        "revision": "abc",
                        "result": result,
                        "effort": "e",
                        "method": "check",
                        "signed_by": "",
                        "requirement": requirement,
                    },
                )
    return project


def test_snapshot_preserves_finished_phase_evidence_and_legacy_checks(project: Project) -> None:
    view = next(e for e in load_snapshot(project).efforts if e.effort == "e")
    finished = next(p for p in view.phases if p.subject == "finished")
    detail = phase_mod.load_phase_detail(project, "e", "finished")
    assert finished.state == "done"
    assert finished.evidence is not None
    assert finished.evidence == detail.evidence
    assert [r.status for r in finished.evidence.requirements] == ["verified", "verified"]
    assert all(r.latest_check is not None for r in finished.evidence.requirements)
    assert all(
        r.latest_check.result == "pass" for r in finished.evidence.requirements if r.latest_check
    )
    current = next(p for p in view.phases if p.subject == "current")
    assert current.evidence is not None
    assert all(
        r.latest_check.result == "fail" for r in current.evidence.requirements if r.latest_check
    )


@pytest.mark.parametrize("reader", ["snapshot", "phase"])
def test_evidence_derivation_scans_only_the_requested_phase(
    project: Project, monkeypatch: pytest.MonkeyPatch, reader: str
) -> None:
    seen: list[tuple[str, list[Record]]] = []
    original = derive.requirement_status

    def observe(
        records: list[Record], phase: str, head: str | None = None
    ) -> dict[str, RequirementStatus]:
        seen.append((phase, records))
        return original(records, phase, head)

    monkeypatch.setattr(phase_mod, "requirement_status", observe)
    monkeypatch.setattr(derive, "requirement_status", observe)
    if reader == "snapshot":
        load_snapshot(project)
    else:
        phase_mod.load_phase_detail(project, "e", "finished")
    assert seen
    for phase, records in seen:
        acceptances = [r for r in records if r["record_type"] == "score:acceptance"]
        ids = {r["id"] for r in acceptances}
        assert acceptances
        assert all(r["payload"].get("phase") == phase for r in acceptances)
        assert all(
            r["payload"].get("criterion_id") in ids
            for r in records
            if r["record_type"] == "tuner:check-run"
        )


@pytest.mark.parametrize("reader", ["snapshot", "phase"])
def test_evidence_derives_requirement_status_once_per_phase(
    project: Project, monkeypatch: pytest.MonkeyPatch, reader: str
) -> None:
    calls: Counter[str] = Counter()
    original = derive.requirement_status

    def observe(
        records: list[Record], phase: str, head: str | None = None
    ) -> dict[str, RequirementStatus]:
        calls[phase] += 1
        return original(records, phase, head)

    monkeypatch.setattr(phase_mod, "requirement_status", observe)
    monkeypatch.setattr(derive, "requirement_status", observe)
    if reader == "snapshot":
        load_snapshot(project)
        assert calls == {"finished": 1, "current": 1}
    else:
        phase_mod.load_phase_detail(project, "e", "finished")
        assert calls == {"finished": 1}


def test_evidence_preserves_equal_timestamp_check_order(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(record_mod, "now", lambda: "2026-11-02T00:00:00+00:00")
    acceptance = project.resolve("score:acceptance", "finished-R1")
    multi = _create(
        project,
        "score:acceptance",
        "finished-multi",
        {
            "method": "check",
            "phase": "finished",
            "effort": "e",
            "verify_command": "true",
            "requirements": ["R1", "R2"],
        },
    )
    for name, criterion, result in (
        ("legacy-tie", acceptance["id"], "fail"),
        ("multi-tie", multi["id"], "pass"),
    ):
        _create(
            project,
            "tuner:check-run",
            name,
            {
                "criterion_id": criterion,
                "revision": "abc",
                "result": result,
                "effort": "e",
                "method": "check",
                "signed_by": "",
                "requirement": "R1",
            },
        )
    tied = [
        r
        for r in phase_mod.list_records(project, "tuner:check-run")
        if r["subject"] in ("legacy-tie", "multi-tie")
    ]
    evidence = phase_mod.load_phase_detail(project, "e", "finished").evidence
    assert evidence is not None
    rows = {row.id: row for row in evidence.requirements}
    assert rows["R1"].latest_check is not None
    assert rows["R1"].latest_check.id == tied[0]["id"]
    assert rows["R1"].status == "unassessed"
    assert rows["R2"].status == "verified"
    snapshot = load_snapshot(project)
    row = next(p for e in snapshot.efforts for p in e.phases if p.subject == "finished")
    assert row.evidence == evidence
