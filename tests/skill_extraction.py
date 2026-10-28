"""Extract `canon` CLI invocations out of skill markdown and check each one
against the schema modules.

Parses fenced bash blocks only. A new invocation starts at each line that
begins with `canon <subcommand>`; everything up to the next such line (or the
end of the fence) belongs to it, so multi-line continuations stay attached.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

_FENCE_RE = re.compile(r"(?ms)^([ \t]*)```(\w*)\n(.*?)^[ \t]*```")
_INVOCATION_START_RE = re.compile(r"(?m)^canon\s+(\S+)")
_PAYLOAD_RE = re.compile(r"--payload\s+'(\{.*?\})'", re.DOTALL)
_KV_RE = re.compile(r"(?:-p|--payload-kv)\s+([A-Za-z_][\w]*)=")

CANON_SUBCOMMANDS = {
    "init", "create", "update", "supersede", "correct", "apply", "get", "list",
    "validate", "schemas",
}
_TYPE_BEARING = {"create", "update", "supersede", "get", "list", "correct"}


def skill_markdown_files(skills_root: Path) -> list[Path]:
    return sorted(skills_root.rglob("*.md"))


def extract_invocations(text: str) -> list[dict]:
    invocations = []
    for indent, language, body in _FENCE_RE.findall(text):
        if language not in ("", "bash"):
            continue
        block = textwrap.dedent(body) if indent else body
        starts = [m.start() for m in _INVOCATION_START_RE.finditer(block)]
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else len(block)
            invocations.append(_parse_chunk(block[start:end]))
    return invocations


def _flag(chunk: str, name: str) -> str | None:
    m = re.search(rf"--{name}\s+(\S+)", chunk)
    return m.group(1).strip("\"'") if m else None


def _parse_chunk(chunk: str) -> dict:
    payload = None
    pm = _PAYLOAD_RE.search(chunk)
    if pm:
        try:
            payload = json.loads(pm.group(1))
        except json.JSONDecodeError:
            payload = None
    return {
        "subcommand": _INVOCATION_START_RE.match(chunk).group(1),
        "type": _flag(chunk, "type"),
        "transition": _flag(chunk, "transition"),
        "rels": re.findall(r"--rel\s+(\S+)", chunk),
        "payload": payload,
        "records": [],
        "raw": chunk.strip(),
    }


def check_invocation(inv: dict, defs: dict[str, dict]) -> list[str]:
    """Return violation messages, or [] if the schema modules permit this invocation."""
    violations: list[str] = []
    sub = inv["subcommand"]
    rtype = inv["type"]

    if sub not in CANON_SUBCOMMANDS:
        return [f"canon {sub}: not a canon subcommand"]
    if inv["rels"]:
        violations.append("--rel is gone: depends_on and informed_by are payload fields")
    if not (sub in _TYPE_BEARING and rtype):
        return violations
    if rtype not in defs:
        return [*violations, f"unknown record type {rtype!r}"]

    record_def = defs[rtype]
    lifecycle = record_def["lifecycle"]
    states = {lifecycle["initial"], *lifecycle["transitions"]}
    states.update(d for dests in lifecycle["transitions"].values() for d in dests)

    if sub == "update" and inv["transition"]:
        dest = inv["transition"]
        reachable = {d for dests in lifecycle["transitions"].values() for d in dests}
        if dest == "superseded" and "supersedes" in record_def["relationships"]:
            violations.append(
                f"update --type {rtype} --transition superseded: use `canon supersede`"
            )
        elif dest not in states:
            violations.append(f"update --type {rtype} --transition {dest!r}: not a lifecycle state")
        elif dest not in reachable:
            violations.append(f"update --type {rtype} --transition {dest!r}: no transition reaches it")

    if sub == "supersede" and "supersedes" not in record_def["relationships"]:
        violations.append(f"supersede --type {rtype}: the lifecycle {lifecycle['name']!r} is not supersedable")
    if sub == "correct" and lifecycle["name"] != "event":
        violations.append(f"correct --type {rtype}: only event types take corrections")

    payload = inv["payload"]
    if payload is not None and sub in {"create", "update", "supersede", "correct"}:
        unknown = sorted(set(payload) - set(record_def["fields"]))
        if unknown:
            violations.append(f"--type {rtype} --payload has undeclared key(s) {unknown}")
        if sub == "create":
            missing = sorted(set(record_def["required"]) - set(payload))
            if missing:
                violations.append(f"--type {rtype} --payload is missing required field(s) {missing}")
    return violations


def check_skill_text(text: str, defs: dict[str, dict]) -> list[str]:
    messages = []
    for inv in extract_invocations(text):
        for violation in check_invocation(inv, defs):
            first_line = inv["raw"].splitlines()[0]
            messages.append(f"[{first_line}] {violation}")
    return messages
