"""Transform old-format records (project:* types) into canon records."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_FENCE = "---"
_CLOSING_FENCE = "\n---\n"

_PLAN_TYPES = (
    "milestone phase specification design decision constraint work-item "
    "acceptance backlog-item feedback continuity-question"
).split()
_RUN_TYPES = (
    "assignment assignment-amendment execution-report integration-report "
    "assessment release proof-packet failed-attempt"
).split()
_AFF_TYPES = (
    "check-run evidence-observation evidence-binding oracle-amendment "
    "investigation-observation finding"
).split()

TYPE_MAP: dict[str, str] = {
    "project:active-goal": "plan:effort",
    "project:current-position": "plan:position",
    **{f"project:{t}": f"plan:{t}" for t in _PLAN_TYPES},
    **{f"project:{t}": f"run:{t}" for t in _RUN_TYPES},
    **{f"project:{t}": f"aff:{t}" for t in _AFF_TYPES},
}

LIST_FIELDS: dict[str, tuple[str, ...]] = {
    "plan:work-item": ("decisions", "requirements"),
    "plan:design": ("decisions",),
    "plan:specification": ("requirements",),
    "plan:acceptance": ("test_ids", "oracle_hashes"),
    "plan:effort": ("merged_from",),
    "aff:check-run": ("failing_node_ids",),
    "aff:evidence-observation": ("claim_ids",),
    "aff:oracle-amendment": ("old_hashes", "new_hashes"),
}

REFERENCE_FIELDS: dict[str, str] = {
    "phase": "plan:phase",
    "milestone": "plan:milestone",
    "work_item": "plan:work-item",
    "assignment": "run:assignment",
    "acceptance": "plan:acceptance",
    "effort": "plan:effort",
}
REFERENCE_LIST_FIELDS: dict[str, str] = {"decisions": "plan:decision"}

DROPPED_ENVELOPE_KEYS = ("base_kind", "identity", "stewardship", "epistemic_status")
KEPT_RELATIONSHIPS = ("supersedes", "corrects")
MOVED_RELATIONSHIPS = ("informed_by", "contradicted_by")
DEPENDS_ON_MARKER = "$rec"


class LegacyError(ValueError):
    pass


def _split_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, str):
        if value.lstrip().startswith("["):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                decoded = None
            if isinstance(decoded, list):
                return [str(item) for item in decoded]
        return [part.strip() for part in value.split(",") if part.strip()]
    raise LegacyError(f"cannot read a list from {value!r}")


def transform_record(old: dict[str, Any]) -> dict[str, Any]:
    old_type = old.get("record_type")
    if old_type not in TYPE_MAP:
        raise LegacyError(f"{old.get('id')}: unknown old type {old_type!r}")
    new_type = TYPE_MAP[old_type]

    out = {k: copy.deepcopy(v) for k, v in old.items() if k not in DROPPED_ENVELOPE_KEYS}
    out["record_type"] = new_type
    payload = out["payload"] = dict(out.get("payload") or {})

    if new_type == "plan:effort":
        payload.pop("scope", None)
    if "subject" in payload:
        if payload["subject"] != out.get("subject"):
            raise LegacyError(
                f"{old.get('id')}: payload.subject {payload['subject']!r} differs from envelope subject {out.get('subject')!r}"
            )
        del payload["subject"]
    for field in LIST_FIELDS.get(new_type, ()):
        if field in payload:
            payload[field] = _split_list(payload[field])

    relationships: dict[str, list[str]] = {}
    for name, ids in (old.get("relationships") or {}).items():
        ids = list(ids or [])
        if name in KEPT_RELATIONSHIPS:
            if ids:
                relationships[name] = ids
        elif name in MOVED_RELATIONSHIPS:
            if ids:
                payload[name] = ids
        elif name == "depends_on":
            if ids:
                payload["depends_on"] = [{DEPENDS_ON_MARKER: i} for i in ids]
        else:
            raise LegacyError(f"{old.get('id')}: unknown relationship {name!r}")
    out["relationships"] = relationships
    return out


def _unresolved(record: dict[str, Any], field: str, value: Any) -> dict[str, Any]:
    return {
        "record": record.get("id"),
        "record_type": record.get("record_type"),
        "subject": record.get("subject"),
        "field": field,
        "value": value,
    }


def transform_store(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    new_records = [transform_record(r) for r in records]
    by_id = {r["id"]: r for r in new_records}
    subjects: dict[str, set[str]] = {}
    for r in new_records:
        subjects.setdefault(r["record_type"], set()).add(r["subject"])

    unresolved: list[dict[str, Any]] = []

    for r in new_records:
        payload = r["payload"]

        if "depends_on" in payload:
            resolved: list[str] = []
            for item in payload["depends_on"]:
                if not (isinstance(item, dict) and DEPENDS_ON_MARKER in item):
                    resolved.append(item)
                    continue
                target = by_id.get(item[DEPENDS_ON_MARKER])
                if target is None:
                    unresolved.append(_unresolved(r, "depends_on", item[DEPENDS_ON_MARKER]))
                elif target["subject"] not in resolved:
                    resolved.append(target["subject"])
            if resolved:
                payload["depends_on"] = resolved
            else:
                del payload["depends_on"]

        assignment = payload.get("assignment")
        if r["record_type"].startswith("run:") and isinstance(assignment, str) and assignment.startswith("rec-"):
            target = by_id.get(assignment)
            if target is None:
                unresolved.append(_unresolved(r, "assignment", assignment))
            else:
                payload["assignment"] = target["subject"]

        for field in MOVED_RELATIONSHIPS:
            for value in payload.get(field, []):
                if value not in by_id:
                    unresolved.append(_unresolved(r, field, value))
        for field in KEPT_RELATIONSHIPS:
            for value in r["relationships"].get(field, []):
                if value not in by_id:
                    unresolved.append(_unresolved(r, f"relationships.{field}", value))

    for r in new_records:
        payload = r["payload"]
        for field, target_type in REFERENCE_FIELDS.items():
            value = payload.get(field)
            if isinstance(value, str) and value and value not in subjects.get(target_type, ()):
                unresolved.append(_unresolved(r, field, value))
        for field, target_type in REFERENCE_LIST_FIELDS.items():
            for value in payload.get(field, []) or []:
                if value not in subjects.get(target_type, ()):
                    unresolved.append(_unresolved(r, field, value))
        for value in payload.get("depends_on", []):
            if value not in subjects.get(r["record_type"], ()):
                unresolved.append(_unresolved(r, "depends_on", value))

    counts = Counter(f"{o['record_type']} -> {n['record_type']}" for o, n in zip(records, new_records))
    report = {
        "total": len(new_records),
        "counts": dict(sorted(counts.items())),
        "unresolved": unresolved,
    }
    return new_records, report


def parse_record_text(text: str, path: Path | str) -> dict[str, Any]:
    if not text.startswith(f"{_FENCE}\n"):
        raise LegacyError(f"{path}: expected {_FENCE!r} as the first line")
    rest = text[len(_FENCE) + 1 :]
    idx = rest.find(_CLOSING_FENCE)
    if idx == -1:
        raise LegacyError(f"{path}: missing closing {_FENCE!r} fence")
    try:
        obj = json.loads(rest[:idx])
    except json.JSONDecodeError as exc:
        raise LegacyError(f"{path}: malformed frontmatter JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise LegacyError(f"{path}: frontmatter must be a JSON object")
    remainder = rest[idx + len(_CLOSING_FENCE) :]
    obj["body"] = remainder[1:] if remainder.startswith("\n") else remainder
    return obj


def _read_tree(root: Path, pattern: str) -> list[dict[str, Any]]:
    paths = sorted(root.glob(pattern))
    known = set(paths)
    unread = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p not in known)
    if unread:
        raise LegacyError(f"{root}: files this migration cannot read: {unread[:5]}")
    return [parse_record_text(path.read_text(encoding="utf-8"), path) for path in paths]


def read_records(records_dir: Path | str) -> list[dict[str, Any]]:
    return _read_tree(Path(records_dir), "*/*.md")


LEGACY_FILES = ("meta.json", "project-design.json", "resolved-contract.json")
LEGACY_DIRS = ("records", "history", "log", "views")


def read_history(history_dir: Path | str) -> list[dict[str, Any]]:
    return _read_tree(Path(history_dir), "*/*/*.md")


def transform_history(
    snapshots: list[dict[str, Any]], records: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """Transform old history snapshots; drop dependency ids no record explains."""
    subject_of = {r["id"]: r["subject"] for r in records + snapshots}
    out: list[dict[str, Any]] = []
    dropped = 0
    for snapshot in snapshots:
        new = transform_record(snapshot)
        payload = new["payload"]
        if "depends_on" in payload:
            resolved: list[str] = []
            for item in payload["depends_on"]:
                subject = subject_of.get(item[DEPENDS_ON_MARKER]) if isinstance(item, dict) else item
                if subject is None:
                    dropped += 1
                elif subject not in resolved:
                    resolved.append(subject)
            if resolved:
                payload["depends_on"] = resolved
            else:
                del payload["depends_on"]
        assignment = payload.get("assignment")
        if isinstance(assignment, str) and assignment.startswith("rec-") and assignment in subject_of:
            payload["assignment"] = subject_of[assignment]
        out.append(new)
    return out, dropped


def _legacy_settings(design_path: Path) -> dict[str, Any]:
    if not design_path.is_file():
        return {}
    phase_gate = json.loads(design_path.read_text(encoding="utf-8")).get("phase_gate")
    return {"run": {"phase_gate": phase_gate}} if phase_gate else {}


def _stray_views_dir(store_root: Path) -> Path | None:
    nested = store_root / ".artifacts"
    if nested.is_dir() and {p.name for p in nested.iterdir()} <= {"views"}:
        return nested
    return None


def migrate_store(
    store_root: Path | str,
    namespaces: list[str],
    *,
    installed: dict[str, Any] | None = None,
    allow_errors: bool = False,
) -> dict[str, Any]:
    """Rebuild an old-format store as a canon store, in place.

    The new store is built and validated in a staging directory beside the old
    one. The old store changes only when validation passes, or when
    `allow_errors` is set.
    """
    import shutil

    from canon.revision import with_revision
    from canon.record_file import prepare_record
    from canon.schema import SchemaSet
    from canon.store import Store
    from canon.sync import init_store
    from canon.validation import validate_store

    store_root = Path(store_root)
    if (store_root / "config.json").exists():
        raise LegacyError(f"{store_root} is already a canon store")
    if not (store_root / "meta.json").is_file():
        raise LegacyError(f"{store_root} has no legacy store (meta.json is missing)")

    old_records = read_records(store_root / "records")
    old_history = read_history(store_root / "history")
    records, report = transform_store(old_records)
    history, dropped = transform_history(old_history, old_records)

    staging = store_root.parent / f".{store_root.name}.canon-staging"
    if staging.exists():
        shutil.rmtree(staging)
    store = Store(staging)
    try:
        init_store(store, namespaces, installed)
        settings = _legacy_settings(store_root / "project-design.json")
        if settings:
            config = store.load_config()
            config["settings"] = settings
            store.write_config(config)
        schemas = SchemaSet.load(staging, store.load_config())
        for snapshot in history:
            store.archive_history(with_revision(prepare_record(snapshot)))
        for record in records:
            stamped = with_revision(prepare_record(record))
            store.create_record(stamped)
            type_def = schemas.types.get(stamped["record_type"])
            if type_def is not None and type_def.lifecycle.appends_only:
                store.archive_history(stamped)
        errors = validate_store(schemas, store_root=staging, immutability=False)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    report.update(
        {
            "store": str(store_root),
            "history": len(history),
            "history_dropped_dependencies": dropped,
            "errors": errors,
        }
    )
    if errors and not allow_errors:
        shutil.rmtree(staging)
        report["status"] = "invalid"
        return report

    for name in LEGACY_DIRS:
        shutil.rmtree(store_root / name, ignore_errors=True)
    for name in LEGACY_FILES:
        (store_root / name).unlink(missing_ok=True)
    stray = _stray_views_dir(store_root)
    if stray is not None:
        shutil.rmtree(stray)
    for child in staging.iterdir():
        child.rename(store_root / child.name)
    staging.rmdir()
    report["status"] = "migrated" if not errors else "migrated_with_errors"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run the legacy record transform.")
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", required=True)
    args = parser.parse_args(argv)
    _, report = transform_store(read_records(args.records_dir))
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
