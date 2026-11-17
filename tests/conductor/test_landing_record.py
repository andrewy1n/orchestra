from __future__ import annotations

import json


def test_landing_record_is_registered_in_the_synced_store_schema() -> None:
    from conftest import REPO_ROOT

    source = json.loads(
        (REPO_ROOT / "orchestra/conductor/schemas/conductor.json").read_text(encoding="utf-8")
    )
    synced = json.loads((REPO_ROOT / ".canon/schemas/conductor.json").read_text(encoding="utf-8"))

    assert "landing" in source["types"]
    assert synced["types"]["landing"] == source["types"]["landing"]
