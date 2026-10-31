"""Verify lossless transfer of a store into a temporary SQLite database."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.revision import compute_revision
from orchestra.canon.errors import StoreError
from orchestra.canon.transfer import export_ops, import_ops


def verify(source: Backend) -> tuple[int, int]:
    errors: list[str] = []
    records = list(source.iter_records(errors=errors))
    count = len(records) + len(errors)
    history = list(source.read_history())
    mismatches = len(errors)
    for error in errors:
        print(error)
    with tempfile.TemporaryDirectory(prefix="canon-verify-import-") as scratch:
        root = Path(scratch)
        target = open_backend(root, {"backend": "sqlite"})
        export = root / "transfer.jsonl"
        try:
            with export.open("w", encoding="utf-8", newline="\n") as out:
                export_ops(source, out)
            with export.open(encoding="utf-8") as src:
                import_ops(target, src)
        except (StoreError, ValueError, OSError) as exc:
            print(f"Import failed: {exc}")
            return count, mismatches + 1
        for record in records:
            try:
                imported = target.read_record(record["record_type"], record["id"])
                if imported != record or compute_revision(record) != record["revision"]:
                    mismatches += 1
            except StoreError:
                mismatches += 1
        imported_records = list(target.iter_records())
        source_keys = {(record["record_type"], record["id"]) for record in records}
        mismatches += sum(
            (record["record_type"], record["id"]) not in source_keys for record in imported_records
        )
        imported_history: dict[tuple[str, str, str], dict[str, Any]] = {
            (record["record_type"], record["id"], record["revision"]): record
            for record in target.read_history()
        }
        for record in history:
            key = (record["record_type"], record["id"], record["revision"])
            if (
                imported_history.pop(key, None) != record
                or compute_revision(record) != record["revision"]
            ):
                mismatches += 1
        mismatches += len(imported_history)
        print(f"{len(history)} retained history revisions checked")
    return count, mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_store", type=Path)
    args = parser.parse_args()
    try:
        count, mismatches = verify(open_backend(args.source_store))
    except (StoreError, ValueError, OSError) as exc:
        print(f"Verification failed: {exc}")
        count, mismatches = 0, 1
    print(f"{count} records, {mismatches} mismatches")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
