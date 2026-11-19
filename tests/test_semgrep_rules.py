from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

VENDOR = Path(__file__).resolve().parents[1] / ".semgrep" / "vendor"


def test_secrets_snapshot_matches_recorded_checksum_and_rule_count() -> None:
    snapshot = (VENDOR / "secrets.yml").read_bytes()
    manifest = json.loads((VENDOR / "snapshot.lock").read_text())
    parsed = yaml.safe_load(snapshot)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()

    assert hashlib.sha256(snapshot).hexdigest() == manifest["sha256"]
    assert hashlib.sha256(canonical).hexdigest() == manifest["parsed_sha256"]
    assert len(parsed["rules"]) == manifest["rules"]
    assert manifest["source"] == "https://semgrep.dev/c/p/secrets"
    assert (VENDOR / "LICENSE").is_file()
