"""HTTP oracles for the web dashboard.

The page is the JSON from GET /api/snapshot. Writes are POST /api/needs and
POST /api/backlog on the FastAPI app `dashboard.backend.server.create_app` builds for that store.
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import helpers as h
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server.app import create_app  # noqa: E402
from dashboard.backend import backlog as backlog_module  # noqa: E402
from dashboard.backend import dismiss as dismiss_module  # noqa: E402
from dashboard.backend import snapshot as snapshot_mod  # noqa: E402


def _phase(cli, defs, effort: str, subject: str, ordinal: int, *states: str) -> dict:
    record = h.create_generic_record(
        cli,
        defs,
        "score:phase",
        subject=subject,
        extra_payload={"title": f"title of {subject}", "ordinal": ordinal, "effort": effort},
    )
    if states:
        record = h.transition(cli, "score:phase", record, *states)
    return record


def _seed(cli, defs) -> None:
    h.create_generic_record(
        cli,
        defs,
        "score:effort",
        subject="alpha",
        extra_payload={"goal": "ship alpha", "kind": "deliver"},
    )
    _phase(cli, defs, "alpha", "p-work", 1, "in_progress")
    _phase(cli, defs, "alpha", "route-phase", 2, "in_progress")
    _phase(cli, defs, "alpha", "merge-phase", 3, "in_progress", "done")
    h.create_generic_record(
        cli,
        defs,
        "score:work-item",
        subject="task-ready",
        extra_payload={
            "title": "title of task-ready",
            "phase": "p-work",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "attempts": 0,
            "estimate_minutes": 0,
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "score:continuity-question",
        subject="alpha",
        extra_payload={"blocking": True, "scope": "which backend"},
    )
    h.create_generic_record(
        cli,
        defs,
        "tuner:finding",
        subject="human-finding",
        extra_payload={
            "claim": "a human must decide",
            "basis": "observed",
            "needs": "human",
            "effort": "alpha",
            "invalidated_when": "decision recorded",
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "tuner:check-run",
        subject="unsigned-check",
        extra_payload={
            "method": "manual",
            "signed_by": "",
            "result": "pass",
            "effort": "alpha",
            "revision": "abc",
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "score:specification",
        subject="route-spec",
        extra_payload={
            "phase": "route-phase",
            "effort": "alpha",
            "requirements": ["R1"],
            "weight": "light",
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "conductor:assessment",
        subject="route-phase-R1",
        extra_payload={
            "requirement": "R1",
            "phase": "route-phase",
            "effort": "alpha",
            "missing": "",
            "confidence": "high",
            "status": "failed",
            "next": "design",
            "level": "design",
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "conductor:integration-report",
        subject="route-phase-report",
        extra_payload={
            "phase": "route-phase",
            "effort": "alpha",
            "result": "fail",
            "revision": "dirty",
        },
    )
    h.create_generic_record(
        cli,
        defs,
        "composer:idea",
        subject="park-me",
        extra_payload={"effort": "alpha", "status": "open", "source": "chat"},
    )


def _model_item(snap: snapshot_mod.Snapshot, kind: str) -> snapshot_mod.NeedsYouItem:
    matches = [item for view in snap.efforts for item in view.needs_you if item.kind == kind]
    assert len(matches) == 1, [item.kind for view in snap.efforts for item in view.needs_you]
    return matches[0]


def _backlog_item(snap: snapshot_mod.Snapshot) -> snapshot_mod.BacklogItem:
    matches = [item for view in snap.efforts for item in view.backlog]
    assert len(matches) == 1
    return matches[0]


def _snapshot(target) -> snapshot_mod.Snapshot:
    loaded = None
    try:
        loaded = snapshot_mod.load_snapshot(target)
    except ImportError:
        loaded = None
    assert loaded is not None, "dashboard.backend.snapshot.load_snapshot is not importable"
    return loaded


@contextmanager
def _running(store):
    target = open_store(store)
    yield TestClient(create_app(target), raise_server_exceptions=False), target


def _request(
    method: str, client: TestClient, path: str, payload: dict | None = None
) -> tuple[int, bytes]:
    response = client.request(method, path, json=payload)
    return response.status_code, response.content


def _get_json(client: TestClient, path: str) -> dict:
    status, body = _request("GET", client, path)
    assert 200 <= status < 300, (status, body)
    return json.loads(body)


def _post(client: TestClient, path: str, payload: dict) -> int:
    status, _body = _request("POST", client, path, payload)
    return status


def _page_needs(payload: dict, kind: str) -> dict:
    matches = [
        item for view in payload["efforts"] for item in view["needs_you"] if item["kind"] == kind
    ]
    assert len(matches) == 1, payload
    return matches[0]


def _assert_same_snapshot(payload: dict, snap: snapshot_mod.Snapshot) -> None:
    assert [view["effort"] for view in payload["efforts"]] == [view.effort for view in snap.efforts]
    for raw, view in zip(payload["efforts"], snap.efforts):
        assert raw["goal"] == view.goal
        assert [(row["id"], row["subject"]) for row in raw["phases"]] == [
            (row.id, row.subject) for row in view.phases
        ]
        assert [(row["id"], row["subject"], row["status"]) for row in raw["tasks"]] == [
            (row.id, row.subject, row.status) for row in view.tasks
        ]
        assert [(row["id"], row["kind"], row["revision"]) for row in raw["needs_you"]] == [
            (row.id, row.kind, row.revision) for row in view.needs_you
        ]
        assert [(row["id"], row["subject"], row["status"]) for row in raw["backlog"]] == [
            (row.id, row.subject, row.status) for row in view.backlog
        ]


def _stored(cli, record_type: str, record_id: str) -> dict:
    result = cli("get", "--type", record_type, "--id", record_id)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    record = payload.get("record") if isinstance(payload.get("record"), dict) else payload
    assert record.get("id") == record_id
    return record


def _revision(cli, record_type: str, record_id: str) -> str:
    return _stored(cli, record_type, record_id)["revision"]


@pytest.fixture()
def defs(resolved_contract):
    return h.record_defs_by_id(resolved_contract)


def test_r3_snapshot(store, cli, defs):
    _seed(cli, defs)
    snap = _snapshot(open_store(store))
    assert {item.kind for view in snap.efforts for item in view.needs_you} >= {
        "blocking-question",
        "needs-human",
        "unsigned-check",
        "loop-route",
        "integration",
    }
    assert any(view.phases for view in snap.efforts)
    assert any(view.tasks for view in snap.efforts)
    assert any(view.backlog for view in snap.efforts)
    with _running(store) as (client, _target):
        _assert_same_snapshot(_get_json(client, "/api/snapshot"), snap)


def test_r4_token(store, cli, defs):
    _seed(cli, defs)
    target = open_store(store)
    with _running(store) as (client, served):
        assert Path(served.store_path).resolve() == Path(target.store_path).resolve()
        payload = _get_json(client, "/api/token")
        assert payload["token"] == snapshot_mod.change_token(target)


def test_r21_approve(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    snap = _snapshot(open_store(store))
    question = _model_item(snap, "blocking-question")
    assert question.revision and question.revision != "@current"
    calls = []

    def spy(target, item, *, signer=None, action=None, note=None):
        calls.append(
            {"target": target, "item": item, "signer": signer, "action": action, "note": note}
        )

    monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
    with _running(store) as (client, target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "blocking-question")
        assert page["id"] == question.id
        assert page["revision"] == question.revision
        status = _post(
            client,
            "/api/needs",
            {"id": page["id"], "action": "approve", "revision": page["revision"]},
        )
    assert 200 <= status < 300, status
    assert len(calls) == 1
    assert calls[0]["action"] == "approve"
    assert isinstance(calls[0]["item"], snapshot_mod.NeedsYouItem)
    assert calls[0]["item"].id == question.id
    assert calls[0]["item"].kind == "blocking-question"
    assert calls[0]["item"].revision == page["revision"]
    assert Path(calls[0]["target"].store_path).resolve() == Path(target.store_path).resolve()


def test_r22_reject_note(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    question = _model_item(_snapshot(open_store(store)), "blocking-question")
    assert question.revision and question.revision != "@current"
    calls = []

    def spy(target, item, *, signer=None, action=None, note=None):
        calls.append({"item": item, "action": action, "note": note})

    monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
    with _running(store) as (client, _target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "blocking-question")
        assert page["revision"] == question.revision
        missing = _post(
            client,
            "/api/needs",
            {"id": page["id"], "action": "reject", "revision": page["revision"]},
        )
        blank = _post(
            client,
            "/api/needs",
            {
                "id": page["id"],
                "action": "reject",
                "revision": page["revision"],
                "note": "   ",
            },
        )
        assert missing >= 400 and blank >= 400
        assert calls == []
        noted = _post(
            client,
            "/api/needs",
            {
                "id": page["id"],
                "action": "reject",
                "revision": page["revision"],
                "note": "approach is wrong",
            },
        )
    assert 200 <= noted < 300, noted
    assert len(calls) == 1
    assert calls[0]["action"] == "reject"
    assert calls[0]["note"] == "approach is wrong"
    assert isinstance(calls[0]["item"], snapshot_mod.NeedsYouItem)
    assert calls[0]["item"].revision == page["revision"]


def test_r23_sign(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    check = _model_item(_snapshot(open_store(store)), "unsigned-check")
    assert check.revision and check.revision != "@current"
    calls = []

    def spy(target, item, *, signer=None, action=None, note=None):
        calls.append({"item": item, "action": action, "signer": signer})

    monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
    with _running(store) as (client, _target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "unsigned-check")
        assert page["id"] == check.id
        assert page["revision"] == check.revision
        status = _post(
            client, "/api/needs", {"id": page["id"], "action": "sign", "revision": page["revision"]}
        )
    assert 200 <= status < 300, status
    assert len(calls) == 1
    assert calls[0]["action"] == "sign"
    assert isinstance(calls[0]["item"], snapshot_mod.NeedsYouItem)
    assert calls[0]["item"].id == check.id
    assert calls[0]["item"].revision == page["revision"]


def test_r24_signer(store, cli, defs, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_SIGNED_BY", "oracle-signer")
    assert dismiss_module.default_signer() == "oracle-signer"
    _seed(cli, defs)
    check = _model_item(_snapshot(open_store(store)), "unsigned-check")
    original = dismiss_module.dismiss_item
    calls = []

    def spy(target, item, *, signer=None, action=None, note=None):
        calls.append({"item": item, "action": action, "signer": signer})
        return original(target, item, signer=signer, action=action, note=note)

    monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
    with _running(store) as (client, _target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "unsigned-check")
        assert page["revision"] == check.revision
        status = _post(
            client,
            "/api/needs",
            {
                "id": page["id"],
                "action": "sign",
                "revision": page["revision"],
                "signer": "intruder",
            },
        )
    assert 200 <= status < 300, status
    assert len(calls) == 1
    assert calls[0]["action"] == "sign"
    assert calls[0]["item"].revision == page["revision"]
    assert calls[0]["signer"] in (None, "oracle-signer")
    assert calls[0]["signer"] != "intruder"
    # Sign uses canon `correct`: signed_by lands on the correction
    # successor, not the predecessor id returned by get --id <original>.
    listed = cli("list", "--type", check.record_type, "--subject", check.subject, "--full")
    assert listed.returncode == 0, listed.stdout + listed.stderr
    rows = json.loads(listed.stdout).get("records", [])
    tips = [row for row in rows if check.id in (row.get("relationships") or {}).get("corrects", [])]
    assert len(tips) == 1, [(row.get("id"), row.get("relationships")) for row in rows]
    signed = tips[0]
    assert signed["payload"]["signed_by"] == dismiss_module.default_signer()
    assert signed["payload"]["signed_by"] != "intruder"


def test_r25_accept_note(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    finding = _model_item(_snapshot(open_store(store)), "needs-human")
    assert finding.revision and finding.revision != "@current"
    calls = []

    def spy(target, item, *, signer=None, action=None, note=None):
        calls.append({"item": item, "action": action, "note": note})

    monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
    with _running(store) as (client, _target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "needs-human")
        assert page["revision"] == finding.revision
        missing = _post(
            client,
            "/api/needs",
            {"id": page["id"], "action": "accept", "revision": page["revision"]},
        )
        blank = _post(
            client,
            "/api/needs",
            {
                "id": page["id"],
                "action": "accept",
                "revision": page["revision"],
                "note": " ",
            },
        )
        assert missing >= 400 and blank >= 400
        assert calls == []
        noted = _post(
            client,
            "/api/needs",
            {
                "id": page["id"],
                "action": "accept",
                "revision": page["revision"],
                "note": "accepted residual risk",
            },
        )
    assert 200 <= noted < 300, noted
    assert len(calls) == 1
    assert calls[0]["action"] == "accept"
    assert calls[0]["note"] == "accepted residual risk"
    assert isinstance(calls[0]["item"], snapshot_mod.NeedsYouItem)
    assert calls[0]["item"].id == finding.id
    assert calls[0]["item"].revision == page["revision"]


def test_r26_refused(store, cli, defs):
    _seed(cli, defs)
    target = open_store(store)
    snap = _snapshot(target)
    loop = _model_item(snap, "loop-route")
    integration = _model_item(snap, "integration")
    before = snapshot_mod.change_token(target)
    loop_rev = _revision(cli, loop.record_type, loop.id)
    integration_rev = _revision(cli, integration.record_type, integration.id)
    with _running(store) as (client, _served):
        page = _get_json(client, "/api/snapshot")
        for kind in ("loop-route", "integration"):
            item = _page_needs(page, kind)
            status = _post(
                client,
                "/api/needs",
                {"id": item["id"], "action": "approve", "revision": item["revision"]},
            )
            assert status >= 400, (kind, status)
        merge = _post(
            client,
            "/api/needs",
            {
                "id": "merge:merge-phase",
                "kind": "merge-branch",
                "action": "approve",
                "revision": "",
            },
        )
        assert merge >= 400, merge
    assert snapshot_mod.change_token(target) == before
    assert _revision(cli, loop.record_type, loop.id) == loop_rev
    assert _revision(cli, integration.record_type, integration.id) == integration_rev


def test_r28_backlog_dismiss(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    parked = _backlog_item(_snapshot(open_store(store)))
    assert parked.status == "open"
    calls = []

    def spy(target, item):
        calls.append({"target": target, "item": item})

    monkeypatch.setattr(backlog_module, "dismiss_item", spy)
    with _running(store) as (client, target):
        page = _get_json(client, "/api/snapshot")
        raw = next(
            item for view in page["efforts"] for item in view["backlog"] if item["id"] == parked.id
        )
        assert raw["status"] == "open"
        status = _post(client, "/api/backlog", {"id": raw["id"], "action": "dismiss"})
    assert 200 <= status < 300, status
    assert len(calls) == 1
    assert isinstance(calls[0]["item"], snapshot_mod.BacklogItem)
    assert calls[0]["item"].id == parked.id
    assert calls[0]["item"].status == "open"
    assert Path(calls[0]["target"].store_path).resolve() == Path(target.store_path).resolve()


def test_r29_backlog_promote(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    parked = _backlog_item(_snapshot(open_store(store)))
    assert parked.status == "open"
    calls = []

    def spy(target, item, *, phase=None):
        calls.append({"target": target, "item": item, "phase": phase})

    monkeypatch.setattr(backlog_module, "promote_item", spy)
    with _running(store) as (client, target):
        page = _get_json(client, "/api/snapshot")
        raw = next(
            item for view in page["efforts"] for item in view["backlog"] if item["id"] == parked.id
        )
        status = _post(client, "/api/backlog", {"id": raw["id"], "action": "promote"})
    assert 200 <= status < 300, status
    assert len(calls) == 1
    assert isinstance(calls[0]["item"], snapshot_mod.BacklogItem)
    assert calls[0]["item"].id == parked.id
    assert calls[0]["item"].status == "open"
    assert Path(calls[0]["target"].store_path).resolve() == Path(target.store_path).resolve()


def test_r34_stale(store, cli, defs, monkeypatch):
    _seed(cli, defs)
    question = _model_item(_snapshot(open_store(store)), "blocking-question")
    displayed = question.revision
    assert displayed and displayed != "@current"

    def boom(target, item, *, signer=None, action=None, note=None):
        raise dismiss_module.DismissError(dismiss_module.STALE_MESSAGE)

    monkeypatch.setattr(dismiss_module, "dismiss_item", boom)
    with _running(store) as (client, target):
        page = _page_needs(_get_json(client, "/api/snapshot"), "blocking-question")
        assert page["id"] == question.id
        assert page["revision"] == displayed
        before = snapshot_mod.change_token(target)
        status = _post(
            client,
            "/api/needs",
            {"id": page["id"], "action": "approve", "revision": page["revision"]},
        )
        assert status >= 400, status
        assert snapshot_mod.change_token(target) == before
    assert _revision(cli, question.record_type, question.id) == displayed
