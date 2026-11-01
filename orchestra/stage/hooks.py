"""Session hooks: inject the handoff at start, block on new validation errors at stop."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import TextIO, TypeGuard

from orchestra import views
from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project, StoreBindingError, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.model_types import PlanningPayload

PROTOCOL = (
    "This project keeps its state as canon records. Views are derived: edit "
    "records, not view output. Capture at the event with `canon`. Render views "
    "with `orchestra handoff`, `orchestra view plan|status|verification` and "
    "`orchestra brief <work-item>`. Before you finish, run `canon validate` "
    "and fix every error."
)

HOOK_CONTEXT_BUDGET = 9000
MAX_HOOK_CONSTRAINTS = 20
MAX_CONSTRAINT_STATEMENT_CHARS = 220

CLAUDE = "--claude"
CURSOR = "--cursor"


def _is_json_object(value: object) -> TypeGuard[JsonObject]:
    return isinstance(value, dict)


def _is_json_array(value: object) -> TypeGuard[list[JsonValue]]:
    return isinstance(value, list)


def read_hook_input(stream: TextIO) -> JsonObject:
    try:
        value: object = json.load(stream)
    except Exception:
        return {}
    return value if _is_json_object(value) else {}


def _root_from_hook(data: JsonObject, fmt: str) -> Path:
    if fmt == CLAUDE:
        cwd = data.get("cwd")
        start = Path(cwd) if isinstance(cwd, str) and cwd else Path.cwd()
    else:
        roots = data.get("workspace_roots")
        first_root = roots[0] if isinstance(roots, list) and roots else None
        start = Path(first_root) if isinstance(first_root, str) else Path.cwd()
    return start.resolve()


def _open_project(root: Path) -> Project | None:
    try:
        return open_store(root)
    except StoreBindingError:
        return None


def baseline_path(root: Path, data: JsonObject) -> Path | None:
    session = data.get("session_id") or data.get("conversation_id")
    if not session:
        return None
    directory = os.environ.get("ORCHESTRA_BASELINE_DIR")
    base = Path(directory) if directory else Path(tempfile.gettempdir()) / "orchestra-baselines"
    key = hashlib.sha256(f"{root}\0{session}".encode()).hexdigest()[:24]
    return base / f"{key}.json"


def _save_baseline(project: Project, root: Path, data: JsonObject) -> None:
    path = baseline_path(root, data)
    if path is None:
        return
    try:
        errors = project.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(errors))
    except Exception:
        return


def _load_baseline(root: Path, data: JsonObject) -> set[str] | None:
    path = baseline_path(root, data)
    if path is None or not path.is_file():
        return None
    try:
        value: object = json.loads(path.read_text())
        if _is_json_array(value):
            return {str(item) for item in value}
        return None
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _constraint_lines(records: list[Record]) -> list[str]:
    items, total = views.hook_constraints(records, MAX_HOOK_CONSTRAINTS)
    if not items:
        return []
    lines = ["", "Active constraints:"]
    for item in items:
        payload: PlanningPayload = item.get("payload") or {}  # pyright: ignore[reportAssignmentType]  # Constraint schemas validate these payload fields.
        statement = (payload.get("statement") or "").strip()
        if len(statement) > MAX_CONSTRAINT_STATEMENT_CHARS:
            statement = statement[:MAX_CONSTRAINT_STATEMENT_CHARS].rstrip() + "…"
        lines.append(f"- **{item.get('subject')}**: {statement}")
    if total > len(items):
        lines.append(f"(+{total - len(items)} more not shown)")
    return lines


def _assemble_start(constraint_lines: list[str], sections: list[tuple[str, str]]) -> str:
    def build(shown: list[str], omitted: list[str]) -> str:
        parts = [
            PROTOCOL,
            *constraint_lines,
            "",
            "\n\n".join(["# Project Handoff", *shown]),
        ]
        if omitted:
            parts.extend(
                [
                    "",
                    f"Not shown: {', '.join(omitted)}. Run `orchestra handoff --effort <slug>`.",
                ]
            )
        parts.extend(["", "Other views: `orchestra view plan|status|verification`."])
        return "\n".join(parts).strip() + "\n"

    count = 0
    while count < len(sections):
        shown = [text for _, text in sections[: count + 1]]
        omitted = [name for name, _ in sections[count + 1 :]]
        if len(build(shown, omitted)) > HOOK_CONTEXT_BUDGET:
            break
        count += 1
    return build(
        [text for _, text in sections[:count]],
        [name for name, _ in sections[count:]],
    )


def _wrap_start(fmt: str, ctx: str) -> JsonObject:
    if fmt == CLAUDE:
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": ctx,
            }
        }
    return {"additional_context": ctx}


def cmd_start(fmt: str, data: JsonObject) -> JsonObject | None:
    root = _root_from_hook(data, fmt)
    try:
        project = _open_project(root)
        if project is None:
            return None
        if open_backend(project.store_path).backup_due(timedelta(hours=24)):
            subprocess.run(["canon", "backup"], cwd=root, check=True)
        records = views.load_records(project)
        _save_baseline(project, root, data)
        ctx = _assemble_start(_constraint_lines(records), views.hook_handoff_sections(records))
    except Exception as exc:
        ctx = f"orchestra session-start failed: {exc}\n"
    return _wrap_start(fmt, ctx)


def cmd_stop(fmt: str, data: JsonObject) -> JsonObject | None:
    if fmt == CLAUDE:
        if data.get("stop_hook_active"):
            return {}
    else:
        if data.get("status") != "completed":
            return {}
        loop_count = data.get("loop_count", 0)
        if not isinstance(loop_count, (int, float)):
            raise TypeError(
                f"'>' not supported between instances of '{type(loop_count).__name__}' and 'int'"
            )
        if loop_count > 0:
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
            f"\n\n({earlier} error(s) already present when this session started are not shown.)"
        )
    return _block(fmt, message)


def _block(fmt: str, message: str) -> JsonObject:
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
