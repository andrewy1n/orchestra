from __future__ import annotations

import hashlib
import json


def failure_key(criterion_id: str, failing_node_ids: list[str]) -> str:
    digest = json.dumps([criterion_id, sorted(failing_node_ids)], separators=(",", ":"))
    return hashlib.sha256(digest.encode()).hexdigest()
