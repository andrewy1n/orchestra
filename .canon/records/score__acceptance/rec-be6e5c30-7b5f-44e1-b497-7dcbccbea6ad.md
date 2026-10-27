---
{
  "id": "rec-be6e5c30-7b5f-44e1-b497-7dcbccbea6ad",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "close_batch validates request-carried red_check_run_id and copied red fields; it does not query the store for prior check-runs",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "red-first",
    "requirement": "R2",
    "verify_command": "uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_request"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-10T23:44:06+00:00",
  "relationships": {},
  "revision": "sha256:8c4e82e2f698bb52576e718d3da6770cc06da515050d3835d4ea503df6c35a9e",
  "subject": "close-red-first-request",
  "time": {
    "as_of": "2026-10-10T23:44:06+00:00"
  }
}
---

