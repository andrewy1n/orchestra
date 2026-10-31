"""Verify a pre-cutover export is preserved in a SQLite store."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from orchestra.canon.backend import open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.revision import compute_revision


def verify(export: Path, store_root: Path) -> tuple[Counter[str], Counter[str]]:
    store = open_backend(store_root)
    current = {(r["record_type"], r["id"]): r for r in store.iter_records()}
    history = {
        (r["record_type"], r["id"], r["revision"]): r for r in store.read_history()
    }
    ops = {
        (record_id, op["seq"]): op
        for record_id, chain in store.iter_chains()
        for op in chain
    }
    seen: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    keys: set[tuple[str, str]] = set()
    final: dict[tuple[str, str], tuple[int, str | None]] = {}
    for line in export.read_text(encoding="utf-8").splitlines():
        envelope = json.loads(line)
        key = (envelope["record_type"], envelope["record_id"])
        op = envelope["op"]
        keys.add(key)
        seen["ops"] += 1
        if ops.get((key[1], envelope["seq"])) != op:
            failures["op missing or changed"] += 1
        snapshots = list(envelope.get("history", []))
        if isinstance(op.get("record"), dict):
            snapshots.append(op["record"])
        for snapshot in snapshots:
            seen["revisions"] += 1
            if compute_revision(snapshot) != snapshot["revision"]:
                failures["export revision hash invalid"] += 1
            if history.get((*key, snapshot["revision"])) != snapshot and (
                current.get(key) != snapshot
            ):
                failures["revision missing or changed"] += 1
        if envelope["seq"] >= final.get(key, (0, None))[0]:
            record = op.get("record")
            final[key] = (envelope["seq"], record["revision"] if record else None)
    seen["records"] = len(keys)
    seen["live records"] = len(current)
    seen["live records not in export"] = len(set(current) - keys)
    seen["export final revision still current"] = sum(
        1
        for key, (_, rev) in final.items()
        if key in current and current[key]["revision"] == rev
    )
    failures["record id missing"] = sum(key not in current for key in keys)
    return seen, +failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("store_root", type=Path)
    args = parser.parse_args()
    try:
        seen, failures = verify(args.export, args.store_root)
    except (StoreError, ValueError, KeyError, OSError) as exc:
        print(f"Verification failed: {exc}")
        return 1
    print(f"export sha256 {hashlib.sha256(args.export.read_bytes()).hexdigest()}")
    for name, value in seen.items():
        print(f"{name}: {value}")
    print(f"{sum(failures.values())} mismatches {dict(failures) or ''}".rstrip())
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
