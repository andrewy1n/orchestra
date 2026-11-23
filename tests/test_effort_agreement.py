from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project
from conftest import git
from fastapi.testclient import TestClient

from dashboard.backend.server import schemas
from dashboard.backend.server.app import create_app
from orchestra.canon import project as project_mod
from orchestra.canon import record as record_mod
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.attention import ATTENTION_ORDER
from orchestra.score.planning.effort import current_effort

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"
SPEC_BODY = "\n\n".join(
    f"## {name}\n\nText."
    for name in (
        "Requirements",
        "Acceptance criteria",
        "Constraints",
        "Non-goals",
        "Invariants",
        "Assumptions",
    )
)
EFFORT = "ef"
HANDOFF_TITLES = {"Unsigned Manual Check": "unsigned-check"}


def _sections(*names: str) -> str:
    return "\n\n".join(f"## {name}\n\nText." for name in names)


FIXED_STAMP = "2030-01-01T00:00:00+00:00"


def _orchestra(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *argv],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _canon(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.canon", "--root", str(cwd), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


def _rewrite(project: Project, record: Record, payload: JsonObject) -> Record:
    store, _ = project._session()
    changed = Record(**record)
    changed["payload"] = payload
    return store.write_record(changed, expected_revision=record["revision"])


def _malform(project: Project, record: Record, **fields: JsonValue) -> Record:
    payload = {key: value for key, value in record["payload"].items() if key not in fields}
    payload.update({key: value for key, value in fields.items() if value is not None})
    return _rewrite(project, record, payload)


def _client(project: Project) -> TestClient:
    return TestClient(create_app(project))


def _snapshot(project: Project) -> dict[str, schemas.EffortSummary]:
    response = _client(project).get("/api/snapshot")
    assert response.status_code == 200, response.text
    body = schemas.SnapshotResponse.model_validate(response.json())
    return {view.effort: view for view in body.efforts}


def _base_store(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "composer:area", "area", {"title": "Area"}, "## Scope\n\nText.")
    create(project, "composer:area", "other-area", {"title": "Other"}, "## Scope\n\nText.")
    create(project, "composer:idea", "idea", {"status": "open", "effort": EFFORT})
    create(project, "composer:placement", EFFORT, {"area": "area"})
    return project


Surface = Callable[[Path, Project], str]


def _cli(*argv: str) -> Surface:
    def run(root: Path, _project: Project) -> str:
        result = _orchestra(root, *argv)
        assert result.returncode != 0, result.stdout
        return result.stderr

    return run


def _route(path: str) -> Surface:
    def run(_root: Path, project: Project) -> str:
        with pytest.raises(RecordShapeError) as raised:
            _client(project).get(path)
        return str(raised.value)

    return run


MALFORMED_READS = [
    pytest.param(
        "score:effort", EFFORT, {"goal": None}, "goal", _cli("handoff"), id="effort-handoff"
    ),
    pytest.param(
        "score:effort", EFFORT, {"goal": None}, "goal", _cli("status"), id="effort-status"
    ),
    pytest.param(
        "score:effort",
        EFFORT,
        {"goal": None},
        "goal",
        _cli("effort", "autonomy", EFFORT, "auto-plan"),
        id="effort-autonomy",
    ),
    pytest.param(
        "score:effort",
        EFFORT,
        {"goal": None},
        "goal",
        _cli("place", EFFORT, "area"),
        id="effort-place",
    ),
    pytest.param(
        "score:effort",
        EFFORT,
        {"goal": None},
        "goal",
        _route("/api/snapshot"),
        id="effort-dashboard",
    ),
    pytest.param(
        "composer:idea", "idea", {"status": None}, "status", _route("/api/areas"), id="idea-areas"
    ),
    pytest.param(
        "composer:idea",
        "idea",
        {"status": None},
        "status",
        _route("/api/snapshot"),
        id="idea-dashboard",
    ),
    pytest.param(
        "composer:area", "area", {"title": 5}, "title", _route("/api/areas"), id="area-areas"
    ),
    pytest.param(
        "composer:area",
        "area",
        {"title": 5},
        "title",
        _cli("place", EFFORT, "area"),
        id="area-place",
    ),
    pytest.param(
        "composer:placement",
        EFFORT,
        {"area": None},
        "area",
        _route("/api/areas"),
        id="placement-areas",
    ),
    pytest.param(
        "composer:placement",
        EFFORT,
        {"area": None},
        "area",
        _route("/api/snapshot"),
        id="placement-dashboard",
    ),
]


@pytest.mark.parametrize(("record_type", "subject", "fields", "field", "surface"), MALFORMED_READS)
def test_malformed_record_fails_with_its_id_and_field_on_every_surface(
    tmp_path: Path,
    record_type: str,
    subject: str,
    fields: dict[str, JsonValue],
    field: str,
    surface: Surface,
) -> None:
    project = _base_store(tmp_path)
    bad = _malform(project, project.resolve(record_type, subject), **fields)

    message = surface(tmp_path, project)

    assert bad["id"] in message
    assert f"field {field}" in message


def _legacy_store(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "score:effort", "second", {"goal": "g2", "kind": "deliver"})
    create(project, "composer:area", "area", {"title": "Area"})
    create(project, "composer:area", "untitled", {"title": "x"})
    create(project, "composer:idea", "idea", {"status": "open", "effort": EFFORT})
    create(project, "composer:idea", "bare", {"status": "open"})
    create(project, "composer:placement", EFFORT, {"area": "area"})
    legacy = project.resolve("composer:area", "untitled")
    _rewrite(project, legacy, {})
    return project


def test_absent_optional_fields_raise_no_error(tmp_path: Path) -> None:
    project = _legacy_store(tmp_path)

    for argv in (
        ("handoff",),
        ("status",),
        ("effort", "autonomy", "second", "auto-plan"),
        ("place", "second", "untitled"),
        ("store", "scan"),
    ):
        result = _orchestra(tmp_path, *argv)
        assert result.returncode == 0, (argv, result.stderr)

    shown = _snapshot(project)
    assert set(shown) == {EFFORT, "second"}
    assert [idea.id for idea in shown[EFFORT].backlog] == [
        project.resolve("composer:idea", "idea")["id"]
    ]
    response = _client(project).get("/api/areas")
    assert response.status_code == 200, response.text
    titles = {row["subject"]: row["title"] for row in response.json()}
    assert titles == {"area": "Area", "untitled": "untitled"}


def _handoff_effort_labels(text: str) -> dict[str, str]:
    return dict(re.findall(r"^## (\S+) \((\w+)\)$", text, re.M))


def test_autonomy_placement_status_and_dashboard_use_one_current_effort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(record_mod, "now", lambda: FIXED_STAMP)
    monkeypatch.setattr(project_mod, "now", lambda: FIXED_STAMP)
    project = make_project(tmp_path)
    first = create(project, "score:effort", EFFORT, {"goal": "old goal", "kind": "deliver"})
    project.supersede(first["id"], payload={"goal": "current goal"})["record"]
    create(project, "score:effort", "gone", {"goal": "gone goal", "kind": "deliver"})
    gone = project.resolve("score:effort", "gone")
    project.supersede(gone["id"], payload={"status": "closed"})
    create(project, "composer:area", "area", {"title": "Area"}, "## Scope\n\nText.")
    create(project, "composer:idea", "idea", {"status": "promoted", "effort": EFFORT})
    create(project, "composer:idea", "gone-idea", {"status": "open", "effort": "gone"})
    assert current_effort(project.records(), EFFORT) is not None
    monkeypatch.undo()

    autonomy = _orchestra(tmp_path, "effort", "autonomy", EFFORT, "auto-plan", "--json")
    assert autonomy.returncode == 0, autonomy.stderr
    placed = _orchestra(tmp_path, "place", EFFORT, "area")
    assert placed.returncode == 0, placed.stderr
    again = _orchestra(tmp_path, "effort", "autonomy", EFFORT, "auto-phases", "--json")
    assert again.returncode == 0, again.stderr

    live = [
        r
        for r in project.list("score:effort")
        if r["subject"] == EFFORT and r["lifecycle_state"] != "superseded"
    ]
    assert len(live) == 1
    assert live[0]["payload"]["goal"] == "current goal"
    assert live[0]["payload"]["autonomy"] == "auto-phases"
    assert live[0]["id"] == json.loads(again.stdout)["record"]

    handoff = _orchestra(tmp_path, "handoff")
    assert handoff.returncode == 0, handoff.stderr
    labels = _handoff_effort_labels(handoff.stdout)
    assert labels == {EFFORT: "live", "gone": "closed"}
    assert "current goal" in handoff.stdout
    assert "old goal" not in handoff.stdout

    shown = _snapshot(project)
    assert set(shown) == {EFFORT}
    assert shown[EFFORT].goal == "current goal"
    assert shown[EFFORT].area == "area"
    areas = _client(project).get("/api/areas").json()
    homes = {idea["subject"]: row["subject"] for row in areas for idea in row["ideas"]}
    assert homes == {"idea": "area"}


def _question(project: Project, scope: str, *, blocking: bool, effort: str = EFFORT) -> Record:
    payload: JsonObject = {"scope": scope, "owner": "human", "blocking": blocking}
    return create(project, "score:continuity-question", effort, payload)


def _attention_store(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    git(tmp_path, "commit", "--allow-empty", "-qm", "init")
    base = git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for name in (EFFORT, "other"):
        create(project, "score:effort", name, {"goal": f"goal {name}", "kind": "deliver"})
    open_phase = create(
        project,
        "score:phase",
        "open-phase",
        {"title": "Open", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY,
    )
    project.update(open_phase["id"], transition="in_progress")
    landing = f"{PHASE_BODY}\n\n## Landing\n\nBranch: phase/shipped\nBase: {base}\n"
    shipped = create(
        project,
        "score:phase",
        "shipped",
        {"title": "Shipped", "ordinal": 2, "effort": EFFORT},
        landing,
    )
    for state in ("in_progress", "done"):
        project.update(shipped["id"], transition=state)
    git(tmp_path, "branch", "phase/shipped")
    git(tmp_path, "switch", "-q", "phase/shipped")
    git(tmp_path, "commit", "--allow-empty", "-qm", "work")
    git(tmp_path, "switch", "-q", base)
    create(
        project,
        "score:specification",
        "open-phase",
        {"phase": "open-phase", "effort": EFFORT, "weight": "full", "requirements": ["R1"]},
        SPEC_BODY,
    )
    _question(project, "blocker", blocking=True)
    _question(project, "loose end", blocking=False)
    create(
        project,
        "tuner:finding",
        "decide",
        {
            "claim": "decide it",
            "basis": "observed",
            "needs": "human",
            "effort": EFFORT,
            "invalidated_when": "decided",
        },
        "## Evidence\n\nText.\n\n## Consequence\n\nText.\n\n## Follow-up\n\nText.",
    )
    acceptance = create(
        project,
        "score:acceptance",
        "manual-a",
        {
            "method": "manual",
            "effort": EFFORT,
            "phase": "open-phase",
            "requirement": "R1",
            "criterion": "looks right",
            "verify_command": "true",
        },
    )
    create(
        project,
        "tuner:check-run",
        "manual-run",
        {
            "criterion_id": acceptance["id"],
            "revision": "abc",
            "result": "pass",
            "effort": EFFORT,
            "method": "manual",
            "signed_by": "",
        },
    )
    create(
        project,
        "conductor:assessment",
        "open-phase",
        {
            "effort": EFFORT,
            "phase": "open-phase",
            "requirement": "R1",
            "status": "blocked",
            "next": "design",
            "confidence": "low",
        },
        _sections("Evidence", "Missing", "Reason"),
    )
    create(
        project,
        "conductor:integration-report",
        "open-phase",
        {"effort": EFFORT, "phase": "open-phase", "result": "fail", "revision": "abc"},
        _sections("Interfaces", "Assumptions", "Invariants", "Conflicts"),
    )
    _question(project, "other-effort", blocking=True, effort="other")
    return project


def _handoff_items(text: str, effort: str) -> list[tuple[str, str, str, str]]:
    section = text.split(f"## {effort} (", 1)[1].split("\n## ", 1)[0]
    items: list[tuple[str, str, str, str]] = []
    for block in section.split("### ")[1:]:
        title, _, rest = block.partition("\n")
        kind = HANDOFF_TITLES.get(title, title.lower().replace(" ", "-"))
        if kind not in ATTENTION_ORDER:
            continue
        for line in rest.splitlines():
            found = re.match(r"- \*\*(.+?)\*\*(?:: (.*))? _\(id: (\S+?)\)_$", line)
            if found:
                items.append((kind, found.group(3), found.group(1), found.group(2) or ""))
    return items


def test_handoff_and_dashboard_list_the_same_attention_items(tmp_path: Path) -> None:
    project = _attention_store(tmp_path)

    handoff = _orchestra(tmp_path, "handoff")
    assert handoff.returncode == 0, handoff.stderr
    from_handoff = _handoff_items(handoff.stdout, EFFORT)
    needs = _snapshot(project)[EFFORT].needs_you
    from_dashboard = [(i.kind, i.id, i.subject, i.text) for i in needs]

    assert [kind for kind, *_ in from_handoff] == list(ATTENTION_ORDER)
    assert from_dashboard == from_handoff
    for _, record_id, *_ in from_dashboard:
        route = _client(project).get(f"/api/needs?effort={EFFORT}&id={record_id}")
        assert route.status_code == 200, route.text


def _written_states(tmp_path: Path) -> tuple[Project, dict[str, Record], dict[str, Record]]:
    project = make_project(tmp_path)
    for name in ("alpha", "beta"):
        create(project, "score:effort", name, {"goal": name, "kind": "deliver"})
    create(project, "composer:area", "area", {"title": "Area"}, "## Scope\n\nText.")
    create(project, "composer:idea", "idea", {"status": "open", "effort": "alpha"})
    create(project, "composer:placement", "alpha", {"area": "area"})
    legacy: JsonObject = {"kind": "deliver"}
    originals: dict[str, Record] = {}
    successors: dict[str, Record] = {}
    for record_type, subject in (
        ("score:effort", "alpha"),
        ("composer:idea", "idea"),
        ("composer:area", "area"),
        ("composer:placement", "alpha"),
    ):
        record = project.resolve(record_type, subject)
        if record_type == "score:effort":
            record = _rewrite(project, record, legacy)
        originals[record["id"]] = record
    beta = project.resolve("score:effort", "beta")
    originals[beta["id"]] = beta
    for record_id, record in originals.items():
        if record["subject"] == "beta":
            payload: JsonObject = {**record["payload"], "goal": "beta corrected"}
        elif record["record_type"] == "composer:idea":
            payload = {**record["payload"], "status": "promoted"}
        elif record["record_type"] == "composer:area":
            payload = {**record["payload"], "title": "Renamed"}
        elif record["record_type"] == "composer:placement":
            payload = {"area": "area"}
        else:
            payload = {"goal": "alpha fixed", "kind": "deliver"}
        successors[record_id] = project.supersede(record_id, payload=payload)["record"]
    return project, originals, successors


def test_canon_get_and_list_return_old_effort_records_unchanged(tmp_path: Path) -> None:
    _project, originals, successors = _written_states(tmp_path)

    listed: dict[str, Record] = {}
    for record_type in ("score:effort", "composer:idea", "composer:area", "composer:placement"):
        result = _canon(tmp_path, "list", "--type", record_type)
        assert result.returncode == 0, result.stderr
        found = json.loads(result.stdout)
        rows = found["records"] if isinstance(found, dict) else found
        listed.update({row["id"]: row for row in rows})

    for record_id, original in originals.items():
        got = _canon(tmp_path, "get", "--id", record_id)
        assert got.returncode == 0, got.stderr
        fetched = json.loads(got.stdout)
        assert fetched["lifecycle_state"] == "superseded"
        for key in ("subject", "record_type", "payload", "body"):
            assert fetched[key] == original.get(key)
        assert json.dumps(fetched["payload"], sort_keys=True) == json.dumps(
            original["payload"], sort_keys=True
        )
        assert listed[record_id]["payload"] == original["payload"]
        assert successors[record_id]["id"] in listed
        assert listed[record_id]["lifecycle_state"] == "superseded"
