"""canon command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from orchestra.canon.backend import open_backend
from orchestra.canon.derive import attach_derived_all, compute_derived
from orchestra.canon.git_backend import GitContextError, assert_git_context
from orchestra.canon.merge import MergeError, merge_store, parse_namespace_map, parse_subject_renames
from orchestra.canon.project import Project, StoreBindingError, open_store
from orchestra.canon.query import (
    QueryError,
    compile_grep,
    order_by_path,
    order_by_recorded_at,
    parse_where,
    record_matches,
    summarize,
)
from orchestra.canon.schema import SchemaError
from orchestra.canon.store import (
    PartialStoreError,
    StaleWriteError,
    StoreError,
    StoreLockError,
    StoreNotInitializedError,
)
from orchestra.canon.sync import add_namespace, init_store, sync_store
from orchestra.canon.transfer import export_ops, import_ops
from orchestra.canon.validation import ValidationError

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_STALE = 2
EXIT_TRANSITION = 3
EXIT_VALIDATION = 4

_CURRENT_REVISION = "@current"
MUTATING_COMMANDS = frozenset(
    {"create", "update", "supersede", "correct", "apply", "init", "merge", "import"}
)
MUTATING_SCHEMA_COMMANDS = frozenset({"sync", "add"})
_TRANSITION_CODES = frozenset({"invalid_transition", "use_supersede", "append_only"})


def _is_read_only(args: argparse.Namespace) -> bool:
    """--read-only, else $CANON_READONLY=1.

    Checked once in main() before any command dispatch, so a refused command
    never opens the store, reads stdin, or touches the filesystem at all.
    """
    if getattr(args, "read_only", False):
        return True
    return os.environ.get("CANON_READONLY") == "1"


def _refuses_write(args: argparse.Namespace) -> bool:
    if args.command in MUTATING_COMMANDS:
        return True
    return args.command == "schemas" and args.schemas_command in MUTATING_SCHEMA_COMMANDS


def _emit_json(data: Any) -> None:
    print(json.dumps(data, indent=2))


def _load_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise StoreError("payload must be a JSON object")
    return data


def _load_payload_args(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload_file = getattr(args, "payload_file", None)
    if payload_file:
        try:
            raw = sys.stdin.read() if payload_file == "-" else Path(payload_file).read_text()
        except OSError as exc:
            raise StoreError(f"cannot read --payload-file {payload_file!r}: {exc}") from exc
        payload.update(_load_payload(raw))
    payload.update(_load_payload(getattr(args, "payload", None)))
    for item in getattr(args, "set_values", None) or []:
        if "=" not in item:
            raise StoreError(f"invalid --set {item!r}; expected key=value")
        key, value = item.split("=", 1)
        if not key:
            raise StoreError(f"invalid --set {item!r}; key must not be empty")
        try:
            payload[key] = json.loads(value)
        except json.JSONDecodeError:
            payload[key] = value
    return payload


class _BodyArgError(Exception):
    pass


def _resolve_body(args: argparse.Namespace) -> tuple[bool, str]:
    """Return (flag_was_given, text). Distinguishes an absent flag from --body ""."""
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body is not None and body_file is not None:
        raise _BodyArgError("--body and --body-file are mutually exclusive")
    if body is not None:
        return True, body
    if body_file is not None:
        if body_file == "-":
            return True, sys.stdin.read()
        try:
            return True, Path(body_file).read_text()
        except OSError as exc:
            raise _BodyArgError(f"cannot read --body-file {body_file!r}: {exc}") from exc
    return False, ""


_TABLE_DEFAULT_FIELDS = (
    "id",
    "record_type",
    "subject",
    "lifecycle_state",
    "revision",
)


def _row_values(record: dict[str, Any], fields: list[str]) -> list[str]:
    values: list[str] = []
    for field in fields:
        if field in record:
            value: Any = record[field]
        else:
            value = record
            for part in field.split("."):
                if not isinstance(value, dict) or part not in value:
                    value = None
                    break
                value = value[part]
        if value is None:
            values.append("")
        elif isinstance(value, (dict, list)):
            values.append(json.dumps(value, sort_keys=True))
        else:
            values.append(str(value))
    return values


def _emit_table(records: list[dict[str, Any]], *, fields: str | None) -> None:
    cols: list[str]
    if fields:
        cols = [field.strip() for field in fields.split(",") if field.strip()]
    elif records:
        # Prefer stable compact columns when present; else union of keys.
        cols = [c for c in _TABLE_DEFAULT_FIELDS if any(c in r for r in records)]
        if not cols:
            cols = sorted({key for record in records for key in record})
    else:
        cols = list(_TABLE_DEFAULT_FIELDS)
    rows = [_row_values(record, cols) for record in records]
    widths = [len(col) for col in cols]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    header = "  ".join(col.ljust(widths[i]) for i, col in enumerate(cols))
    print(header)
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def _emit_tsv(records: list[dict[str, Any]], *, fields: str | None) -> None:
    cols: list[str]
    if fields:
        cols = [field.strip() for field in fields.split(",") if field.strip()]
    elif records:
        cols = [c for c in _TABLE_DEFAULT_FIELDS if any(c in r for r in records)]
        if not cols:
            cols = sorted({key for record in records for key in record})
    else:
        cols = list(_TABLE_DEFAULT_FIELDS)
    print("\t".join(cols))
    for record in records:
        print("\t".join(_row_values(record, cols)))


def _error_response(exc: Exception) -> tuple[dict[str, Any], int]:
    message = str(exc)
    if isinstance(exc, StaleWriteError):
        return {"error": "stale_write", "message": message}, EXIT_STALE
    if isinstance(exc, ValidationError):
        code = exc.code
        return {"error": code, "message": message}, (
            EXIT_TRANSITION if code in _TRANSITION_CODES else EXIT_VALIDATION
        )
    if isinstance(exc, SchemaError):
        return {"error": "schema", "message": message}, EXIT_VALIDATION
    if isinstance(exc, (StoreNotInitializedError, PartialStoreError, StoreBindingError)):
        return {"error": "store_not_ready", "message": message}, EXIT_ERROR
    if isinstance(exc, StoreLockError):
        return {"error": "locked", "message": message}, EXIT_ERROR
    if isinstance(exc, _MissingTarget):
        return {"error": "missing_target", "message": message}, EXIT_ERROR
    if isinstance(exc, StoreError):
        if message.startswith("ambiguous record type"):
            return {"error": "ambiguous_type", "message": message}, EXIT_VALIDATION
        if message.startswith("unknown record type"):
            return {"error": "unknown_type", "message": message}, EXIT_VALIDATION
        if message.startswith("unsafe record type"):
            return {"error": "invalid_type", "message": message}, EXIT_VALIDATION
        if message.startswith("unknown record"):
            return {"error": "not_found", "message": message}, EXIT_ERROR
        if message.startswith("record ") and "', not " in message:
            actual = message.split(" is '", 1)[1].split("', not ", 1)[0]
            return {"error": "wrong_type", "message": message, "actual_type": actual}, EXIT_ERROR
        return {"error": "store", "message": message}, EXIT_ERROR
    raise exc


def _binding_file_present(root: Path) -> bool:
    artifacts = root / ".canon"
    return (artifacts / "store-binding.local.json").exists() or (
        artifacts / "store-binding.json"
    ).exists()


def _command_project(args: argparse.Namespace) -> Project:
    if args.store:
        return open_store(args.root, store=args.store)
    return open_store(args.root)


class _MissingTarget(StoreError):
    pass


def _target(args: argparse.Namespace, project: Project) -> dict[str, Any]:
    if args.id:
        return project.get(args.id, args.type)
    if not args.type or not args.subject:
        raise _MissingTarget("provide --id, or both --type and --subject")
    return project.resolve(args.type, args.subject)


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    try:
        assert_git_context(root)
    except GitContextError as exc:
        _emit_json({"error": "git_context", "message": str(exc)})
        return EXIT_ERROR
    if args.store:
        store_path = Path(args.store)
    else:
        try:
            store_path = open_store(root).store_path
        except StoreBindingError:
            if _binding_file_present(root):
                raise
            store_path = root / ".canon"
    namespaces = [ns.strip() for ns in (args.schemas or "").split(",") if ns.strip()]
    result = init_store(open_backend(store_path), namespaces)
    _emit_json(result)
    return EXIT_OK


def cmd_create(args: argparse.Namespace) -> int:
    project = _command_project(args)
    _, body = _resolve_body(args)
    stored = project.create(
        record_type=args.type,
        subject=args.subject,
        payload=_load_payload_args(args),
        body=body,
    )
    _emit_json({"ok": True, "op": "create", "record": stored, "store": str(project.store_path)})
    return EXIT_OK


def cmd_update(args: argparse.Namespace) -> int:
    project = _command_project(args)
    old = _target(args, project)
    given, body = _resolve_body(args)
    stored = project.update(
        old["id"],
        record_type=old["record_type"],
        transition=args.transition,
        payload=_load_payload_args(args),
        body=body if given else None,
        expected_revision=args.expected_revision,
    )
    _emit_json({"ok": True, "op": "update", "record": stored, "store": str(project.store_path)})
    return EXIT_OK


def cmd_supersede(args: argparse.Namespace) -> int:
    project = _command_project(args)
    old = _target(args, project)
    given, body = _resolve_body(args)
    result = project.supersede(
        old["id"],
        record_type=old["record_type"],
        payload=_load_payload_args(args),
        body=body if given else None,
        expected_revision=args.expected_revision,
    )
    _emit_json({**result, "store": str(project.store_path)})
    return EXIT_OK


def cmd_correct(args: argparse.Namespace) -> int:
    project = _command_project(args)
    old = _target(args, project)
    given, body = _resolve_body(args)
    result = project.correct(
        old["id"],
        record_type=old["record_type"],
        payload=_load_payload_args(args),
        body=body if given else None,
        subject=args.subject,
        expected_revision=args.expected_revision,
    )
    _emit_json({**result, "store": str(project.store_path)})
    return EXIT_OK


def cmd_get(args: argparse.Namespace) -> int:
    project = _command_project(args)
    record = project.get(args.id, args.type)
    if args.body_only:
        print(record.get("body") or "")
    elif args.field:
        value: Any = record
        for part in args.field.split("."):
            if not isinstance(value, dict) or part not in value:
                _emit_json({"error": "field_not_found", "field": args.field})
                return EXIT_ERROR
            value = value[part]
        _emit_json(value)
    else:
        _emit_json(record)
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    project = _command_project(args)
    schemas = project.schemas()
    resolved_type = schemas.resolve_type(args.type) if args.type else None
    try:
        where_filters = parse_where(args.where)
        grep = compile_grep(args.grep)
    except QueryError as exc:
        _emit_json({"error": "invalid_query", "message": str(exc)})
        return EXIT_ERROR
    records = project.records()
    records = attach_derived_all(records, compute_derived(records, schemas))
    if resolved_type:
        records = [record for record in records if record["record_type"] == resolved_type]
    if args.state:
        records = [record for record in records if record["lifecycle_state"] == args.state]
    matched = [
        record
        for record in records
        if record_matches(
            record,
            where_filters=where_filters,
            subject=args.subject,
            exact_subject=args.exact_subject,
            grep=grep,
            since=args.since,
            until=args.until,
            has_inbound_types=args.has_inbound,
        )
    ]
    reverse = bool(args.desc)
    if args.order_by == "recorded_at":
        matched = order_by_recorded_at(matched, reverse=reverse)
    elif args.order_by:
        try:
            matched = order_by_path(matched, args.order_by, reverse=reverse)
        except TypeError as exc:
            _emit_json(
                {"error": "invalid_query", "message": f"cannot order by {args.order_by!r}: {exc}"}
            )
            return EXIT_ERROR
    if args.limit is not None:
        if args.limit < 1:
            _emit_json({"error": "invalid_query", "message": "--limit must be >= 1"})
            return EXIT_ERROR
        matched = matched[: args.limit]
    out_records = matched if args.full else [summarize(record, grep=grep) for record in matched]
    if args.fields:
        fields = [field.strip() for field in args.fields.split(",") if field.strip()]
        projected = []
        for record in out_records:
            item = {}
            for field in fields:
                value: Any = record
                for part in field.split("."):
                    if not isinstance(value, dict) or part not in value:
                        value = None
                        break
                    value = value[part]
                item[field] = value
            projected.append(item)
        out_records = projected
    if args.format == "ndjson":
        for record in out_records:
            print(json.dumps(record))
    elif args.format == "table":
        _emit_table(out_records, fields=args.fields)
    elif args.format == "tsv":
        _emit_tsv(out_records, fields=args.fields)
    else:
        _emit_json({"records": out_records, "count": len(matched)})
    return EXIT_OK


def cmd_apply(args: argparse.Namespace) -> int:
    """Run create, update, supersede, and correct ops from NDJSON.

    Failure semantics are continue-and-report: one bad line does not abort
    the lines around it, and the aggregate result says which lines failed.
    """
    input_arg = args.file or args.input or "-"
    text = sys.stdin.read() if input_arg == "-" else Path(input_arg).read_text()
    operations: list[Any] = []
    op_lines: list[int] = []
    slots: list[dict[str, Any] | None] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            op = json.loads(line)
        except json.JSONDecodeError as exc:
            slots.append({"ok": False, "line": line_no, "error": "json", "message": str(exc)})
            continue
        operations.append(op)
        op_lines.append(line_no)
        slots.append(None)
    project = _command_project(args)
    applied = project.apply(operations)
    applied_results = iter(applied)
    results: list[dict[str, Any]] = []
    op_index = 0
    for slot in slots:
        if slot is not None:
            results.append(slot)
            continue
        result = dict(next(applied_results))
        result["line"] = op_lines[op_index]
        op_index += 1
        results.append(result)
    failed = sum(1 for result in results if not result.get("ok"))
    _emit_json(
        {
            "ok": failed == 0,
            "op": "apply",
            "applied": len(results) - failed,
            "failed": failed,
            "results": results,
            "store": str(project.store_path),
        }
    )
    return EXIT_OK if failed == 0 else EXIT_ERROR


def cmd_validate(args: argparse.Namespace) -> int:
    project = _command_project(args)
    errors = project.validate()
    count = len(project.records()) if not errors else None
    if args.format == "text":
        if errors:
            for error in errors:
                print(error)
        else:
            print(f"valid: {count} records")
    else:
        status = "invalid" if errors else "valid"
        payload: dict[str, Any] = {"status": status, "errors": errors}
        if not errors:
            payload["records"] = count
        _emit_json(payload)
    return EXIT_VALIDATION if errors else EXIT_OK


def cmd_backup(args: argparse.Namespace) -> int:
    project = _command_project(args)
    backend = open_backend(project.store_path)
    path = backend.backup(args.keep)
    _emit_json({"backup": str(path)})
    return EXIT_OK


def cmd_export(args: argparse.Namespace) -> int:
    backend = open_backend(_command_project(args).store_path)
    with Path(args.out).open("w", encoding="utf-8", newline="\n") as out:
        count = export_ops(backend, out)
    _emit_json({"ops": count})
    return EXIT_OK


def cmd_import(args: argparse.Namespace) -> int:
    backend = open_backend(_command_project(args).store_path)
    with Path(args.source).open(encoding="utf-8") as src:
        count = import_ops(backend, src)
    _emit_json({"ops": count})
    return EXIT_OK


def cmd_schemas_sync(args: argparse.Namespace) -> int:
    project = _command_project(args)
    result = sync_store(open_backend(project.store_path))
    _emit_json(result)
    return EXIT_VALIDATION if result["errors"] else EXIT_OK


def cmd_schemas_add(args: argparse.Namespace) -> int:
    project = _command_project(args)
    result = add_namespace(open_backend(project.store_path), args.namespace)
    _emit_json(result)
    return EXIT_VALIDATION if result["errors"] else EXIT_OK


def cmd_merge(args: argparse.Namespace) -> int:
    project = _command_project(args)
    try:
        summary = merge_store(
            open_backend(project.store_path),
            project.schemas(),
            args.source,
            namespaces=parse_namespace_map(args.namespace),
            subject_renames=parse_subject_renames(args.rename_subject),
        )
    except MergeError as exc:
        _emit_json({"error": "merge", "message": str(exc), **exc.details})
        return EXIT_ERROR
    if args.format == "json":
        _emit_json(summary)
    else:
        print("\t".join(["type", "records", "history", "log"]))
        for record_type, row in summary["types"].items():
            print("\t".join([record_type, str(row["records"]), str(row["history"]), str(row["log"])]))
        for item in summary["renamed_subjects"]:
            print(f"renamed {item['record_type']} {item['old']} -> {item['new']}")
        print(f"validation: {summary['status']}")
        for error in summary["errors"]:
            print(error)
    return EXIT_VALIDATION if summary["errors"] else EXIT_OK


def _type_summary(type_def: Any) -> dict[str, Any]:
    return {
        "record_type": type_def.record_type,
        "purpose": type_def.purpose,
        "lifecycle": type_def.lifecycle.name,
        "initial": type_def.lifecycle.initial,
        "transitions": {k: list(v) for k, v in type_def.lifecycle.transitions.items()},
        "fields": type_def.fields,
        "sections": list(type_def.sections),
    }


def cmd_schemas_show(args: argparse.Namespace) -> int:
    schemas = _command_project(args).schemas()
    if args.type:
        _emit_json(_type_summary(schemas.get(schemas.resolve_type(args.type))))
        return EXIT_OK
    if args.namespace:
        if args.namespace not in schemas.modules:
            raise SchemaError(f"namespace {args.namespace!r} is not in this store")
        _emit_json(schemas.modules[args.namespace])
        return EXIT_OK
    _emit_json(
        {
            "schemas": {
                ns: {
                    "version": module["version"],
                    "types": {
                        name: {"purpose": spec["purpose"], "lifecycle": spec["lifecycle"]}
                        for name, spec in module["types"].items()
                    },
                }
                for ns, module in schemas.modules.items()
            }
        }
    )
    return EXIT_OK


def _add_payload_args(p: argparse.ArgumentParser, what: str = "payload") -> None:
    p.add_argument("--payload", help=f"JSON {what} object")
    p.add_argument("--payload-file", help=f"Read JSON {what} from file ('-' for stdin)")
    p.add_argument(
        "-p",
        "--set",
        action="append",
        default=[],
        dest="set_values",
        metavar="key=value",
        help="Set one payload field; the value is JSON-decoded when possible (repeatable)",
    )


def _add_body_args(p: argparse.ArgumentParser, help_text: str) -> None:
    p.add_argument("--body", help=help_text)
    p.add_argument("--body-file", help="Read Markdown body from file ('-' for stdin)")


def _add_target_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--type", help="Qualified or short record type")
    p.add_argument("--id", help="Record id")
    p.add_argument("--subject", help="With --type and no --id, target the latest record with this subject")


def _add_revision_arg(p: argparse.ArgumentParser, default: str | None) -> None:
    p.add_argument(
        "--expected-revision",
        default=default,
        help="Exact revision string, or '@current' to re-read and use whatever is current",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="canon", description="Git-backed typed record store")
    parser.add_argument("--root", default=None, help="Project root (default: cwd)")
    parser.add_argument("--store", default=None, help="Store root path")
    parser.add_argument(
        "--read-only",
        action="store_true",
        dest="read_only",
        help="Refuse every mutating command (init/create/update/supersede/correct/apply/"
        "schemas sync/schemas add); reads still work (default: $CANON_READONLY=1)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a store (requires git context)")
    p_init.add_argument(
        "--schemas",
        help="Comma-separated namespaces of installed schema modules, e.g. score,conductor,tuner",
    )
    p_init.set_defaults(func=cmd_init)

    p_create = sub.add_parser("create", help="Create a new record")
    p_create.add_argument("--type", required=True, help="Qualified or short record type")
    p_create.add_argument("--subject", required=True, help="Record subject")
    _add_payload_args(p_create)
    _add_body_args(p_create, "Markdown body text")
    p_create.set_defaults(func=cmd_create)

    p_update = sub.add_parser("update", help="Transition or patch an existing record")
    _add_target_args(p_update)
    p_update.add_argument(
        "--transition",
        help="Target lifecycle state; omit to patch payload/body in place",
    )
    _add_revision_arg(p_update, _CURRENT_REVISION)
    _add_payload_args(p_update, "payload updates")
    _add_body_args(p_update, "Markdown body text (replaces the current body)")
    p_update.set_defaults(func=cmd_update)

    p_sup = sub.add_parser("supersede", help="Supersede with a new record id")
    _add_target_args(p_sup)
    _add_revision_arg(p_sup, _CURRENT_REVISION)
    _add_payload_args(p_sup, "payload for the successor")
    _add_body_args(p_sup, "Markdown body for the successor (default: the predecessor's body)")
    p_sup.set_defaults(func=cmd_supersede)

    p_correct = sub.add_parser(
        "correct", help="Append a correcting successor to an event record; the original stays"
    )
    _add_target_args(p_correct)
    _add_revision_arg(p_correct, None)
    _add_payload_args(p_correct, "payload overrides for the successor")
    _add_body_args(p_correct, "Markdown body for the successor (default: the original's body)")
    p_correct.set_defaults(func=cmd_correct)

    p_apply = sub.add_parser(
        "apply", help="Run many create/update/supersede/correct ops from NDJSON"
    )
    p_apply.add_argument(
        "input",
        nargs="?",
        default="-",
        help="NDJSON file of {op, type, id, ...} operations, or '-' for stdin (default '-')",
    )
    p_apply.add_argument("--file", help="NDJSON input path (alias for positional input)")
    p_apply.set_defaults(func=cmd_apply)

    p_get = sub.add_parser("get", help="Fetch one record")
    p_get.add_argument("--type", help="Qualified or short record type; narrows a wrong-type error")
    p_get.add_argument("--id", required=True)
    get_shape = p_get.add_mutually_exclusive_group()
    get_shape.add_argument("--field", help="Emit one dot-separated field from the record")
    get_shape.add_argument("--body-only", action="store_true", help="Emit only the Markdown body")
    p_get.set_defaults(func=cmd_get)

    p_list = sub.add_parser("list", help="List records")
    p_list.add_argument("--type")
    p_list.add_argument("--state")
    p_list.add_argument(
        "--where",
        action="append",
        default=[],
        metavar="payload.<field>=<value>",
        help=(
            "Filter by payload.<field> or derived.<field> (repeatable; AND). "
            "Supports =, !=, and =any_of:a,b,c. Nested paths (payload.a.b) walk "
            "dicts. derived fields (e.g. derived.ready) are computed at read time. "
            "Values are JSON-decoded when possible."
        ),
    )
    p_list.add_argument(
        "--subject",
        help="Match records whose subject equals this value, or starts with it (exact-or-prefix)",
    )
    p_list.add_argument(
        "--exact-subject", action="store_true", help="Make --subject an exact-only match"
    )
    p_list.add_argument(
        "--grep", help="Case-insensitive regex match against the record body (not frontmatter fields)"
    )
    p_list.add_argument(
        "--full",
        action="store_true",
        help="Emit full records (including body) instead of the default compact summary",
    )
    p_list.add_argument("--since", help="Only records with recorded_at >= this ISO-8601 timestamp")
    p_list.add_argument("--until", help="Only records with recorded_at <= this ISO-8601 timestamp")
    p_list.add_argument(
        "--has-inbound",
        action="append",
        default=[],
        dest="has_inbound",
        metavar="<relationship_type>",
        help=(
            "Only records with at least one inbound relationship of this type "
            "(derived.referenced_by; repeatable, AND semantics)"
        ),
    )
    p_list.add_argument(
        "--order-by",
        dest="order_by",
        metavar="FIELD",
        help=(
            "Sort matched records by recorded_at, subject, lifecycle_state, "
            "or a dotted payload.<field>/derived.<field> path "
            "(oldest/ascending first; missing values sort first)"
        ),
    )
    p_list.add_argument("--desc", action="store_true", help="Reverse the active --order-by sort")
    p_list.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Return at most N matched records after filter and sort",
    )
    p_list.add_argument("--fields", help="Comma-separated fields to emit (dot paths supported)")
    p_list.add_argument("--format", choices=["json", "ndjson", "table", "tsv"], default="json")
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", help="Validate every record and reference in the store")
    p_validate.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="json prints {status, errors}; text prints one error per line",
    )
    p_validate.set_defaults(func=cmd_validate)

    p_backup = sub.add_parser("backup", help="Back up a SQLite store")
    p_backup.add_argument("--keep", type=int, default=14)
    p_backup.set_defaults(func=cmd_backup)

    p_export = sub.add_parser("export", help="Export deterministic operation JSONL")
    p_export.add_argument("--out", required=True, help="Destination JSONL file")
    p_export.add_argument("--store", default=argparse.SUPPRESS, help="Store root path")
    p_export.set_defaults(func=cmd_export)

    p_import = sub.add_parser("import", help="Import operation JSONL into an empty SQLite store")
    p_import.add_argument("source", help="Source JSONL file")
    p_import.add_argument("--store", default=argparse.SUPPRESS, help="Store root path")
    p_import.set_defaults(func=cmd_import)

    p_schemas = sub.add_parser("schemas", help="Manage the schema modules of a store")
    schemas_sub = p_schemas.add_subparsers(dest="schemas_command", required=True)
    p_sync = schemas_sub.add_parser(
        "sync", help="Copy installed modules into the store, run migrations, then validate"
    )
    p_sync.set_defaults(func=cmd_schemas_sync)
    p_add = schemas_sub.add_parser("add", help="Add an installed module to the store and sync it")
    p_add.add_argument("namespace")
    p_add.set_defaults(func=cmd_schemas_add)
    p_show = schemas_sub.add_parser("show", help="Show the module snapshots a store validates against")
    p_show.add_argument("namespace", nargs="?", help="Print this namespace's full module")
    p_show.add_argument("--type", help="Print one type: purpose, lifecycle, transitions, fields")
    p_show.set_defaults(func=cmd_schemas_show)


    p_merge = sub.add_parser("merge", help="Merge every record of another store into this one")
    p_merge.add_argument("source", help="Source store directory (a .canon-style directory)")
    p_merge.add_argument(
        "--namespace", action="append", default=[], metavar="OLD=NEW", help="Rename a source namespace"
    )
    p_merge.add_argument(
        "--rename-subject",
        action="append",
        default=[],
        metavar="NS:TYPE:OLD=NEW",
        help="Rename a subject, and the references to it, while merging",
    )
    p_merge.add_argument("--format", choices=["table", "json"], default="table")
    p_merge.set_defaults(func=cmd_merge)

    return parser


def _dispatch(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = Path(args.root).resolve() if args.root else Path.cwd()
    if _refuses_write(args) and _is_read_only(args):
        _emit_json(
            {
                "error": "read_only",
                "message": f"{args.command!r} is disabled: runtime is in read-only mode",
            }
        )
        return EXIT_ERROR
    return args.func(args)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (console script, ``python -m orchestra.canon``)."""
    try:
        return _dispatch(argv)
    except json.JSONDecodeError as exc:
        _emit_json({"error": "json", "message": str(exc)})
        return EXIT_ERROR
    except _BodyArgError as exc:
        _emit_json({"error": "invalid_body", "message": str(exc)})
        return EXIT_ERROR
    except (StoreError, ValidationError, StoreBindingError) as exc:
        payload, code = _error_response(exc)
        _emit_json(payload)
        return code
    except Exception as exc:
        _emit_json({"error": "internal", "message": f"{type(exc).__name__}: {exc}"})
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
