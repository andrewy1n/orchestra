---
{
  "id": "rec-fd7dcee3-a0a0-44f8-9fda-fad42f6c1aca",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Through pytest entry point: suite policy modes and gate hardness (none skip, required block, advisory non-block) hold",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "verification-policy",
    "requirement": "R3",
    "verify_command": "uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k \"suite or gate or advisory or policy or mode\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-15T08:46:11+00:00",
  "relationships": {},
  "revision": "sha256:f30d1159e9c348fc03a2f07b1a2a1824066e2944585d5d9d06b7456c0a28c615",
  "subject": "verify-verification-policy",
  "time": {
    "as_of": "2026-10-15T08:46:11+00:00"
  }
}
---

