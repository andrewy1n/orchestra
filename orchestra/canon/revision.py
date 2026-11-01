"""Canonical revision tokens for semantic records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from orchestra.canon.types import Record


def canonical_body(record: Record | Mapping[str, object]) -> dict[str, object]:
    # An empty body is omitted so a bodyless record hashes identically before and
    # after the Markdown format migration.
    return {
        key: value
        for key, value in record.items()
        if key != "revision" and not (key == "body" and not value)
    }


def compute_revision(record: Record | Mapping[str, object]) -> str:
    canonical = json.dumps(canonical_body(record), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"sha256:{digest}"


def with_revision(record: Record) -> Record:
    out: Record = {**record}
    out["revision"] = compute_revision(out)
    return out
