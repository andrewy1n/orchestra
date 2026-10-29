"""Standard-library read surface for the web dashboard.

The Svelte page speaks the spike's GET shapes. This module builds them from
the dashboard loaders behind a change-token cache, exactly the way the
``spikes/web-dashboard`` server did. It uses only the standard library so
``dashboard.backend.server`` imports and serves under the check runner, which has no
FastAPI or uvicorn; ``dashboard.backend.server.app`` wraps the same reader in a FastAPI
app for the launcher.
"""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from dashboard.backend import approval, backlog, dismiss, journal, store
from dashboard.backend.phase import (
    PhaseRow, load_decision_log, load_phase_detail, load_requirement_detail, tabs_for,
)
from dashboard.backend.snapshot import BacklogItem, EffortView, NeedsYouItem, Snapshot, load_snapshot
from dashboard.backend.task import load_task_detail
from orchestra.canon.project import Project


def jsonable(value: Any) -> Any:
    """Recursively convert dataclasses and datetimes to JSON-safe values."""
    if is_dataclass(value) and not isinstance(value, type):
        return jsonable(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def phase_summary(phase: PhaseRow) -> dict:
    evidence = phase.evidence
    verified = None
    requirements = None
    stage = ""
    release_ready = False
    if evidence is not None:
        requirements = len(evidence.requirements)
        verified = sum(row.status == "verified" for row in evidence.requirements)
        stage = evidence.stage
        release_ready = evidence.release_ready
    return {
        "subject": phase.subject,
        "title": phase.title,
        "ordinal": phase.ordinal,
        "state": phase.state,
        "done": phase.done,
        "total": phase.total,
        "id": phase.id,
        "awaiting_signoff": phase.awaiting_signoff,
        "sitting": phase.sitting,
        "elapsed_minutes": phase.elapsed_minutes,
        "unset_estimates": phase.unset_estimates,
        "suite": phase.suite,
        "milestone": phase.milestone,
        "milestone_title": phase.milestone_title,
        "stage": stage,
        "verified": verified,
        "requirements": requirements,
        "release_ready": release_ready,
    }


def effort_summary(view: EffortView) -> dict:
    """One effort as the spike's ``effort_summary`` (plus needs revision)."""
    return {
        "effort": view.effort,
        "goal": view.goal,
        "position": view.position,
        "kind": view.kind,
        "finished": view.finished,
        "release_ready": view.release_ready,
        "phases": [phase_summary(phase) for phase in view.phases],
        "milestones": [jsonable(milestone) for milestone in view.milestones],
        "tasks": [jsonable(task) for task in view.tasks],
        "needs_you": [
            {
                "kind": item.kind,
                "id": item.id,
                "subject": item.subject,
                "text": item.text,
                "record_type": item.record_type,
                "task_id": item.task_id,
                "phase": item.phase,
                "requirement": item.requirement,
                "status": item.status,
                "next": item.next,
                "result": item.result,
                "revision": item.revision,
            }
            for item in view.needs_you
        ],
        "backlog": [
            {
                "id": item.id,
                "subject": item.subject,
                "text": item.text,
                "source": item.source,
                "phase": item.phase,
                "status": item.status,
            }
            for item in view.backlog
        ],
    }


def needs_payload(item: NeedsYouItem) -> dict:
    """One Needs-you item, including its revision and confirm choices."""
    payload = jsonable(item)
    payload["revision"] = item.revision
    payload["approval"] = {
        "confirm_choices": [jsonable(choice) for choice in approval.confirm_choices(item)],
    }
    return payload


class Cache:
    """Snapshot and detail cache keyed by ``dashboard.backend.store.change_token``."""

    def __init__(self, target: Project) -> None:
        self.target = target
        self.lock = threading.Lock()
        self.token = ""
        self.snapshot: Snapshot | None = None
        self.details: dict[tuple, object] = {}

    def _current(self) -> Snapshot:
        token = store.change_token(self.target)
        with self.lock:
            if self.snapshot is not None and token == self.token:
                return self.snapshot
        snapshot = load_snapshot(self.target, token=token)
        with self.lock:
            if token != self.token:
                self.details.clear()
            self.token = snapshot.token or token
            self.snapshot = snapshot
            return snapshot

    def token_only(self) -> str:
        token = store.change_token(self.target)
        with self.lock:
            if token != self.token:
                self.snapshot = None
                self.details.clear()
                self.token = token
            return self.token

    def drop(self) -> None:
        """Clear snapshot and detail cache after a successful write."""
        with self.lock:
            self.snapshot = None
            self.details.clear()
            self.token = ""

    def snapshot_payload(self) -> dict:
        snapshot = self._current()
        return {
            "token": snapshot.token,
            "generated_at": snapshot.generated_at.isoformat(),
            "store": str(self.target.store_path),
            "efforts": [effort_summary(view) for view in snapshot.efforts],
        }

    def effort(self, name: str) -> EffortView:
        snapshot = self._current()
        for view in snapshot.efforts:
            if view.effort == name:
                return view
        raise store.ModelError(f"effort {name} not found")

    def remember(self, key: tuple, load: Callable[[], Any]) -> Any:
        token = self.token_only()
        with self.lock:
            cached = self.details.get((token, key))
        if cached is not None:
            return cached
        value = load()
        with self.lock:
            if self.token == token:
                self.details[(token, key)] = value
        return value


class Reader:
    """Read-only accessors that both the stdlib server and FastAPI app share."""

    def __init__(self, target: Project) -> None:
        self.target = target
        self.cache = Cache(target)

    def token(self) -> dict:
        return {"token": self.cache.token_only()}

    def snapshot(self) -> dict:
        return self.cache.snapshot_payload()

    def phase(self, effort: str, phase: str) -> dict:
        def load() -> dict:
            detail = load_phase_detail(self.target, effort, phase)
            log = load_decision_log(self.target, effort, phase, history=False)
            return {
                "detail": jsonable(detail),
                "tabs": list(tabs_for(detail)),
                "decisions": jsonable(log),
            }

        return self.cache.remember(("phase", effort, phase), load)

    def task(self, task_id: str) -> dict:
        return self.cache.remember(
            ("task", task_id),
            lambda: {"detail": jsonable(load_task_detail(self.target, task_id))},
        )

    def journal(self, effort: str) -> dict:
        def load() -> dict:
            opened, rest = journal.ordered(journal.load_journal(self.target, effort))
            return {"open": [jsonable(item) for item in opened], "rest": [jsonable(item) for item in rest]}

        return self.cache.remember(("journal", effort), load)

    def record(self, record_id: str) -> dict:
        return self.cache.remember(
            ("record", record_id),
            lambda: {"record": jsonable(journal.load_record(self.target, record_id))},
        )

    def requirement(self, effort: str, phase: str, requirement: str) -> dict:
        return self.cache.remember(
            ("requirement", effort, phase, requirement),
            lambda: {"detail": jsonable(load_requirement_detail(self.target, effort, phase, requirement))},
        )

    def needs(self, effort: str, item_id: str) -> dict:
        view = self.cache.effort(effort)
        for item in view.needs_you:
            if item.id == item_id:
                return {"item": needs_payload(item)}
        raise store.ModelError(f"needs-you item {item_id} not found")

    def backlog(self, effort: str, item_id: str) -> dict:
        view = self.cache.effort(effort)
        for item in view.backlog:
            if item.id == item_id:
                return {"item": jsonable(item)}
        raise store.ModelError(f"backlog item {item_id} not found")

    def _find_needs(self, item_id: str, effort: str | None = None) -> NeedsYouItem:
        if effort:
            view = self.cache.effort(effort)
            for item in view.needs_you:
                if item.id == item_id:
                    return item
            raise store.ModelError(f"needs-you item {item_id} not found")
        for view in self.cache._current().efforts:
            for item in view.needs_you:
                if item.id == item_id:
                    return item
        raise store.ModelError(f"needs-you item {item_id} not found")

    def _find_backlog(self, item_id: str, effort: str | None = None) -> BacklogItem:
        if effort:
            view = self.cache.effort(effort)
            for item in view.backlog:
                if item.id == item_id:
                    return item
            raise store.ModelError(f"backlog item {item_id} not found")
        for view in self.cache._current().efforts:
            for item in view.backlog:
                if item.id == item_id:
                    return item
        raise store.ModelError(f"backlog item {item_id} not found")

    def write_needs(self, body: dict) -> dict:
        """POST /api/needs — clear a human Needs-you item through dismiss."""
        item_id = str(body.get("id") or "").strip()
        action = str(body.get("action") or "").strip().lower()
        if not item_id or not action:
            raise WriteError("missing id or action", 400)
        effort = str(body.get("effort") or "").strip() or None
        note_raw = body.get("note")
        note = None if note_raw is None else str(note_raw).strip() or None
        if approval.note_required_for(action) and not note:
            raise WriteError("note required", 400)
        item = self._find_needs(item_id, effort)
        if not dismiss.is_dismissible(item.kind):
            raise WriteError(f"cannot dismiss {item.kind}", 400)
        revision = body.get("revision")
        if revision is not None:
            item = replace(item, revision=str(revision))
        try:
            # Always the process default; ignore any signer field on the body.
            dismiss.dismiss_item(
                self.target,
                item,
                action=action,
                note=note,
                signer=dismiss.default_signer(),
            )
        except dismiss.DismissRefused as exc:
            raise WriteError(str(exc), 400) from exc
        except dismiss.DismissError as exc:
            message = str(exc)
            if message == dismiss.STALE_MESSAGE or "changed since opened" in message.lower():
                raise WriteError(message, 409) from exc
            raise WriteError(message, 400) from exc
        self.cache.drop()
        return {"ok": True}

    def write_backlog(self, body: dict) -> dict:
        """POST /api/backlog — dismiss or promote an open backlog item."""
        item_id = str(body.get("id") or "").strip()
        action = str(body.get("action") or "").strip().lower()
        if not item_id or not action:
            raise WriteError("missing id or action", 400)
        effort = str(body.get("effort") or "").strip() or None
        item = self._find_backlog(item_id, effort)
        try:
            if action == "dismiss":
                backlog.dismiss_item(self.target, item)
            elif action == "promote":
                backlog.promote_item(self.target, item)
            else:
                raise WriteError(f"unsupported action {action!r}", 400)
        except backlog.BacklogRefused as exc:
            raise WriteError(str(exc), 400) from exc
        except backlog.BacklogError as exc:
            raise WriteError(str(exc), 400) from exc
        self.cache.drop()
        return {"ok": True}


class WriteError(Exception):
    """HTTP-mapped failure for a Needs-you or backlog write."""

    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _query(qs: dict, name: str) -> str:
    value = (qs.get(name) or [""])[0]
    if not value:
        raise store.ModelError(f"missing {name}")
    return value


def build_handler(reader: Reader):
    """A ``BaseHTTPRequestHandler`` class serving the read API for one store."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def do_GET(self) -> None:  # noqa: N802 — stdlib spelling
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            try:
                if parsed.path == "/api/token":
                    self._json(reader.token())
                elif parsed.path == "/api/snapshot":
                    self._json(reader.snapshot())
                elif parsed.path == "/api/phase":
                    self._json(reader.phase(_query(qs, "effort"), _query(qs, "phase")))
                elif parsed.path == "/api/task":
                    self._json(reader.task(_query(qs, "id")))
                elif parsed.path == "/api/journal":
                    self._json(reader.journal(_query(qs, "effort")))
                elif parsed.path == "/api/record":
                    self._json(reader.record(_query(qs, "id")))
                elif parsed.path == "/api/requirement":
                    self._json(
                        reader.requirement(_query(qs, "effort"), _query(qs, "phase"), _query(qs, "id"))
                    )
                elif parsed.path == "/api/needs":
                    self._json(reader.needs(_query(qs, "effort"), _query(qs, "id")))
                elif parsed.path == "/api/backlog":
                    self._json(reader.backlog(_query(qs, "effort"), _query(qs, "id")))
                else:
                    self._json({"error": "not found"}, status=404)
            except store.ModelError as exc:
                self._json({"error": str(exc)}, status=404)
            except Exception as exc:  # noqa: BLE001 — surface a failed read
                self._json({"error": str(exc)}, status=500)

        def do_POST(self) -> None:  # noqa: N802 — stdlib spelling
            parsed = urlparse(self.path)
            try:
                body = self._read_json()
                if parsed.path == "/api/needs":
                    self._json(reader.write_needs(body))
                elif parsed.path == "/api/backlog":
                    self._json(reader.write_backlog(body))
                else:
                    self._json({"error": "not found"}, status=404)
            except WriteError as exc:
                self._json({"error": exc.message}, status=exc.status)
            except store.ModelError as exc:
                self._json({"error": str(exc)}, status=404)
            except json.JSONDecodeError as exc:
                self._json({"error": f"invalid json: {exc}"}, status=400)
            except Exception as exc:  # noqa: BLE001 — surface a failed write
                self._json({"error": str(exc)}, status=500)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            if not raw:
                return {}
            data = json.loads(raw.decode())
            if not isinstance(data, dict):
                raise WriteError("JSON body must be an object", 400)
            return data

        def _json(self, payload: dict, status: int = 200) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(target: Project, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """Bind a threading HTTP server for ``target``'s read API and return it.

    The caller runs ``serve_forever()`` in a thread and later calls
    ``shutdown()`` and ``server_close()``.
    """
    return ThreadingHTTPServer((host, port), build_handler(Reader(target)))
