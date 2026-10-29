"""Session hooks: inject the handoff at start, block on new validation errors at stop."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, TextIO

from orchestra import views

PROTOCOL = (
    "This project keeps its state as canon records. Views are derived: edit "
    "records, not view output. Capture at the event with `canon`. Render views "
    "with `orchestra handoff`, `orchestra view plan|status|verification` and "
    "`orchestra brief <work-item>`. Before you finish, run `canon validate` "
    "and fix every error."
)

MAX_HANDOFF_BYTES = 16384
MAX_HOOK_CONSTRAINTS = 8
MAX_CONSTRAINT_STATEMENT_CHARS = 220

CLAUDE = "--claude"
CURSOR = "--cursor"


def read_hook_input(stream: TextIO) -> dict[str, Any]:
    try:
        data = json.load(stream)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _root_from_hook(data: dict[str, Any], fmt: str) -> Path:
    if fmt == CLAUDE:
        start = Path(data.get("cwd") or Path.cwd())
    else:
        roots = data.get("workspace_roots") or []
        start = Path(roots[0]) if roots else Path.cwd()
    return start.resolve()


def _open_project(root: Path):
    from orchestra.canon.project import StoreBindingError, open_store

    try:
        return open_store(root)
    except StoreBindingError:
        return None


def baseline_path(root: Path, data: dict[str, Any]) -> Path | None:
    session = data.get("session_id") or data.get("conversation_id")
    if not session:
        return None
    directory = os.environ.get("ORCHESTRA_BASELINE_DIR")
    base = (
        Path(directory)
        if directory
        else Path(tempfile.gettempdir()) / "orchestra-baselines"
    )
    key = hashlib.sha256(f"{root}\0{session}".encode()).hexdigest()[:24]
    return base / f"{key}.json"


def _save_baseline(project, root: Path, data: dict[str, Any]) -> None:
    path = baseline_path(root, data)
    if path is None:
        return
    try:
        errors = project.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(errors))
    except Exception:
        return


def _load_baseline(root: Path, data: dict[str, Any]) -> set[str] | None:
    path = baseline_path(root, data)
    if path is None or not path.is_file():
        return None
    try:
        return {str(item) for item in json.loads(path.read_text())}
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _truncate(handoff: str) -> str:
    encoded = handoff.encode("utf-8")
    if len(encoded) <= MAX_HANDOFF_BYTES:
        return handoff
    head = encoded[:MAX_HANDOFF_BYTES]
    boundary = head.rfind(b"\n")
    if boundary > 0:
        head = head[:boundary]
    text = head.decode("utf-8", errors="ignore").rstrip()
    return (
        f"{text}\n\n[... handoff truncated at {MAX_HANDOFF_BYTES} bytes; "
        "run `orchestra handoff` for the full handoff ...]"
    )


def _constraint_lines(records: list[dict[str, Any]]) -> list[str]:
    items, total = views.hook_constraints(records, MAX_HOOK_CONSTRAINTS)
    if not items:
        return []
    lines = ["", "Active constraints:"]
    for item in items:
        statement = ((item.get("payload") or {}).get("statement") or "").strip()
        if len(statement) > MAX_CONSTRAINT_STATEMENT_CHARS:
            statement = statement[:MAX_CONSTRAINT_STATEMENT_CHARS].rstrip() + "…"
        lines.append(f"- **{item.get('subject')}**: {statement}")
    if total > len(items):
        lines.append(f"(+{total - len(items)} more not shown)")
    return lines


def _wrap_start(fmt: str, ctx: str) -> dict[str, Any]:
    if fmt == CLAUDE:
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": ctx,
            }
        }
    return {"additional_context": ctx}


def cmd_start(fmt: str, data: dict[str, Any]) -> dict[str, Any] | None:
    root = _root_from_hook(data, fmt)
    try:
        project = _open_project(root)
        if project is None:
            return None
        records = views.load_records(project)
        _save_baseline(project, root, data)
        parts = [PROTOCOL]
        efforts = [text for _, text in views.hook_handoff_sections(records)]
        handoff = "\n\n".join(["# Project Handoff", *efforts])
        parts.extend(["", _truncate(handoff)])
        parts.extend(_constraint_lines(records))
        parts.extend(
            ["", "Other views: `orchestra view plan|status|verification`."]
        )
        ctx = "\n".join(parts).strip() + "\n"
    except Exception as exc:
        ctx = f"orchestra session-start failed: {exc}\n"
    return _wrap_start(fmt, ctx)


def cmd_stop(fmt: str, data: dict[str, Any]) -> dict[str, Any] | None:
    if fmt == CLAUDE:
        if data.get("stop_hook_active"):
            return {}
    elif data.get("status") != "completed" or data.get("loop_count", 0) > 0:
        return {}
    root = _root_from_hook(data, fmt)
    try:
        project = _open_project(root)
    except Exception as exc:
        return _block(fmt, f"Session-end store check failed:\n\n{exc}")
    if project is None:
        return None
    try:
        errors = project.validate()
    except Exception as exc:
        return _block(fmt, f"Session-end store check failed:\n\n{exc}")
    if not errors:
        return {}
    baseline = _load_baseline(root, data)
    earlier = 0
    if baseline is not None:
        new = [error for error in errors if error not in baseline]
        if not new:
            return {}
        earlier = len(errors) - len(new)
        errors = new
    message = "Session-end store check failed:\n\n" + "\n".join(errors)
    if earlier:
        message += (
            f"\n\n({earlier} error(s) already present when this session "
            "started are not shown.)"
        )
    return _block(fmt, message)


def _block(fmt: str, message: str) -> dict[str, Any]:
    if fmt == CLAUDE:
        return {"decision": "block", "reason": message}
    return {"followup_message": message}


def run(command: str, fmt: str, stdin: TextIO | None = None) -> int:
    data = read_hook_input(stdin if stdin is not None else sys.stdin)
    handler = cmd_start if command == "hook-start" else cmd_stop
    out = handler(fmt, data)
    if out is not None:
        print(json.dumps(out))
    return 0
