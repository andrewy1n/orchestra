"""Pure operation-chain helpers used by SQLite import and transfer."""

from __future__ import annotations

from typing import Any


def fold(ops: list[dict[str, Any]]) -> Any | None:
    current = None
    for op in ops:
        if op.get("outcome") == "accepted":
            current = op["record"]
    return current
