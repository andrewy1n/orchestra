"""Contract-driven helpers shared by the test modules.

Nothing here hardcodes today's record type names or counts — every helper
walks whatever `records`/`bundles` the resolved contract currently declares,
so the suite keeps working as the contract gains or changes record types.
"""

from __future__ import annotations

import itertools
import json
import subprocess
import sys
from collections import deque
from typing import Any

from conftest import REPO_ROOT

_COUNTER = itertools.count()

# The CLI has no clock option, so shift datetime.now inside a CLI subprocess to write a past recorded_at.
_PAST_CLOCK = """
import datetime as _dt, runpy, sys
_real = _dt.datetime
class _Past(_real):
    @classmethod
    def now(cls, tz=None):
        return _real.now(tz) - _dt.timedelta(hours=48)
_dt.datetime = _Past
sys.argv = ["canon", *sys.argv[1:]]
runpy.run_module("orchestra.canon", run_name="__main__", alter_sys=True)
"""


def skill_text(name: str) -> str:
    skill = REPO_ROOT / "skills" / name
    parts = [skill / "SKILL.md", *sorted((skill / "references").glob("*.md"))]
    return "\n\n".join(path.read_text() for path in parts)


def run_cli_48h_ago(store, *args: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", _PAST_CLOCK, "--root", str(store), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def schema_defs() -> dict[str, dict]:
    """Record type definitions from the schema modules, keyed by qualified type."""
    from orchestra.canon.modules import discover

    defs: dict[str, dict] = {}
    for module in discover().values():
        from orchestra.canon.schema import type_defs

        for record_type, type_def in type_defs(module.module).items():
            fields = type_def.fields
            required = {n: f for n, f in fields.items() if not f.get("optional")}
            lifecycle = type_def.lifecycle
            defs[record_type] = {
                "id": record_type,
                "name": record_type.split(":", 1)[1],
                "purpose": type_def.purpose,
                "fields": fields,
                "required": required,
                "payload": [n for n in fields if n != "depends_on"],
                "optional_payload": [
                    n for n, f in fields.items() if f.get("optional") and n != "depends_on"
                ],
                "payload_enum": {n: f["enum"] for n, f in fields.items() if "enum" in f},
                "payload_references": {
                    n: _ref_targets(f)[0] for n, f in fields.items() if _ref_targets(f)
                },
                "required_sections": list(type_def.sections),
                "relationships": ["supersedes"]
                if lifecycle.supersedable or lifecycle.name == "current"
                else [],
                "lifecycle": {
                    "name": lifecycle.name,
                    "initial": lifecycle.initial,
                    "transitions": {k: list(v) for k, v in lifecycle.transitions.items()},
                },
            }
    return defs


GENERIC_EFFORT = "test-effort"


def generic_effort(cli, defs) -> str:
    """Subject of a closed effort shared by records that name no effort of their own."""
    found = cli("list", "--type", "score:effort", "--subject", GENERIC_EFFORT)
    if not json.loads(found.stdout)["records"]:
        closed_effort(cli, defs, GENERIC_EFFORT)
    return GENERIC_EFFORT


def closed_effort(cli, defs, subject: str) -> dict:
    """An effort the dashboard treats as no longer live."""
    effort = create_generic_record(cli, defs, "score:effort", subject=subject)
    result = cli(
        "supersede",
        "--type",
        "score:effort",
        "--id",
        effort["id"],
        "--expected-revision",
        effort["revision"],
        "--payload",
        json.dumps({**effort["payload"], "status": "closed"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def csv(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def with_rels(cli, payload: dict, rels) -> dict:
    """Fold legacy `depends_on:<id>` and `informed_by:<id>` links into the payload."""
    merged = dict(payload)
    for rel in rels or ():
        kind, _, target = rel.partition(":")
        if kind == "depends_on":
            found = cli("get", "--id", target)
            assert found.returncode == 0, found.stdout + found.stderr
            merged.setdefault("depends_on", []).append(json.loads(found.stdout)["subject"])
        elif kind == "informed_by":
            merged.setdefault("informed_by", []).append(target)
        else:
            raise AssertionError(f"unsupported link {rel!r}")
    return merged


def record_def(name: str) -> dict:
    """The definition of the type with this unqualified name."""
    return next(d for d in schema_defs().values() if d["name"] == name)


def _ref_targets(form: dict) -> list[str]:
    inner = form.get("list", form)
    if "ref" not in inner:
        return []
    value = inner["ref"]
    return list(value) if isinstance(value, list) else [value]


def transition(cli, record_type: str, record: dict, *states: str) -> dict:
    for state in states:
        result = cli(
            "update",
            "--type",
            record_type,
            "--id",
            record["id"],
            "--transition",
            state,
            "--expected-revision",
            record["revision"],
        )
        assert result.returncode == 0, result.stdout + result.stderr
        record = json.loads(result.stdout)["record"]
    return record


def record_defs_by_id(contract: dict) -> dict[str, dict]:
    return {r["id"]: r for r in contract["records"]}


def advertises_supersedes(record_def: dict) -> bool:
    return "supersedes" in record_def.get("relationships", [])


def generic_payload_value(field: str) -> Any:
    return f"test-{field}"


def generic_body(record_def: dict) -> str | None:
    required = record_def.get("required_sections") or []
    if not required:
        return None
    parts = [f"## {name}\n\nplaceholder text for {name}." for name in required]
    return "\n\n".join(parts)


def unique_subject(record_def: dict) -> str:
    name = record_def["name"]
    return f"test-{name}-{next(_COUNTER)}"


def _generic_value(cli, defs, field: str, form: dict, target_cache: dict[str, dict]) -> Any:
    if "list" in form:
        return []
    if "ref" in form:
        target_type = _ref_targets(form)[0]
        if target_type == "score:effort":
            return generic_effort(cli, defs)
        if target_type not in target_cache:
            target_cache[target_type] = create_generic_record(
                cli, defs, target_type, target_cache=target_cache
            )
        target = target_cache[target_type]
        return target["id"] if form.get("pin") else target["subject"]
    if "enum" in form:
        return form["enum"][0]
    kind = form["type"]
    if kind in ("integer", "number"):
        return 1
    if kind == "boolean":
        return True
    return generic_payload_value(field)


def ensure_refs(cli, defs, record_def: dict, given: dict) -> None:
    """Create a generic record for each subject reference in `given` that has no record yet."""
    for field, value in given.items():
        form = record_def["fields"].get(field)
        if not form or form.get("pin") or not value:
            continue
        inner = form.get("list", form)
        if "ref" not in inner or inner.get("pin"):
            continue
        target_type = _ref_targets(inner)[0]
        for subject in value if isinstance(value, list) else [value]:
            found = cli("list", "--type", target_type, "--subject", subject)
            if found.returncode == 0 and json.loads(found.stdout).get("records"):
                continue
            assert target_type != "score:decision", (
                f"create decision {subject!r} before the record that cites it"
            )
            context = {
                k: given[k] for k in ("effort",) if k in given and k in defs[target_type]["fields"]
            }
            create_generic_record(
                cli, defs, target_type, subject=subject, extra_payload=context or None
            )


def create_generic_record(
    cli,
    defs: dict[str, dict],
    record_type: str,
    *,
    subject: str | None = None,
    extra_payload: dict | None = None,
    target_cache: dict[str, dict] | None = None,
) -> dict:
    """Create a minimal-but-valid record of `record_type`, recursively
    satisfying any `payload_references` it declares. Returns the parsed
    `record` dict from the CLI's JSON response.
    """
    if target_cache is None:
        target_cache = {}
    record_def = defs[record_type]
    subject = subject or unique_subject(record_def)
    payload: dict[str, Any] = {}
    for field, form in record_def["required"].items():
        if extra_payload and field in extra_payload:
            continue
        payload[field] = _generic_value(cli, defs, field, form, target_cache)
    if extra_payload:
        payload.update(extra_payload)
        ensure_refs(cli, defs, record_def, extra_payload)
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    body = generic_body(record_def)
    if body:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, (
        f"create {record_type} failed (exit {result.returncode}): {result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]


def transitions_graph(record_def: dict) -> dict[str, list[str]]:
    return record_def.get("lifecycle", {}).get("transitions", {}) or {}


def all_edges(record_def: dict) -> list[tuple[str, str]]:
    graph = transitions_graph(record_def)
    return [(src, dest) for src, dests in graph.items() for dest in dests]


def shortest_path(record_def: dict, target_state: str) -> list[str]:
    """BFS shortest path of states from the lifecycle's initial state to
    `target_state`, inclusive of both endpoints."""
    initial = record_def["lifecycle"]["initial"]
    if target_state == initial:
        return [initial]
    graph = transitions_graph(record_def)
    frontier = deque([[initial]])
    seen = {initial}
    while frontier:
        path = frontier.popleft()
        node = path[-1]
        for nxt in graph.get(node, []):
            if nxt in seen:
                continue
            new_path = [*path, nxt]
            if nxt == target_state:
                return new_path
            seen.add(nxt)
            frontier.append(new_path)
    raise AssertionError(f"no path from {initial!r} to {target_state!r} in {graph!r}")


def drive_to_state(cli, defs: dict[str, dict], record_type: str, target_state: str) -> dict:
    """Create a fresh record of `record_type` and drive it along a shortest
    path to `target_state`, using `supersede` where the contract requires it
    and plain `update --transition` otherwise. Returns the record dict at
    `target_state` (note: `supersede` mints a new id, so the returned record's
    id can differ from the one `create` produced)."""
    record_def = defs[record_type]
    path = shortest_path(record_def, target_state)
    record = create_generic_record(cli, defs, record_type)
    for dest in path[1:]:
        record = _apply_transition(cli, record_def, record_type, record, dest)
    assert record["lifecycle_state"] == target_state
    return record


def _apply_transition(cli, record_def: dict, record_type: str, record: dict, dest: str) -> dict:
    """Drive `record` from its current state to `dest` and return the record
    that actually reached `dest`.

    `supersede` reaches "superseded" by retiring the *old* id (the new id it
    mints stays at the initial state) -- so for that op the record "at dest"
    is the predecessor, read back fresh to prove the write really landed.
    """
    if dest == "superseded" and advertises_supersedes(record_def):
        result = cli(
            "supersede",
            "--type",
            record_type,
            "--id",
            record["id"],
            "--expected-revision",
            record["revision"],
            "--payload",
            json.dumps(record["payload"]),
        )
        assert result.returncode == 0, (
            f"supersede {record_type} -> {dest} failed (exit {result.returncode}): "
            f"{result.stdout}\n{result.stderr}"
        )
        readback = cli("get", "--type", record_type, "--id", record["id"])
        assert readback.returncode == 0, readback.stdout + readback.stderr
        return json.loads(readback.stdout)
    result = cli(
        "update",
        "--type",
        record_type,
        "--id",
        record["id"],
        "--transition",
        dest,
        "--expected-revision",
        record["revision"],
    )
    assert result.returncode == 0, (
        f"transition {record_type} -> {dest} failed (exit {result.returncode}): "
        f"{result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]
