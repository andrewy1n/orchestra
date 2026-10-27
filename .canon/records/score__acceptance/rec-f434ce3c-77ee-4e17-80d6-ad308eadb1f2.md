---
{
  "id": "rec-f434ce3c-77ee-4e17-80d6-ad308eadb1f2",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "The tier-2 check-run carries runner metadata: revision = phase head SHA, exit_code, duration_s, output_sha256, and failing node IDs when failed, with evidence_kind integration",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "tiered-verification",
    "requirement": "R3",
    "verify_command": "uv run --with pytest python -m pytest tests/test_tiered_verification.py -q -k \"meta or fields or evidence_kind or digest\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-11T09:34:43+00:00",
  "relationships": {},
  "revision": "sha256:026e05c5f8da6be04d2ddc03ba692c2fcaa5ad08d4edc0b20580ea7afe8253cc",
  "subject": "tier2-engine-meta",
  "time": {
    "as_of": "2026-10-11T09:34:43+00:00"
  }
}
---

