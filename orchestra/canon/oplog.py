"""Pure operation-chain helpers used by SQLite import and transfer."""

from __future__ import annotations

from orchestra.canon.types import Record, StoredOp


def fold(ops: list[StoredOp]) -> Record | None:
    current = None
    for op in ops:
        if op.get("outcome") == "accepted":
            current = op["record"]
    return current
