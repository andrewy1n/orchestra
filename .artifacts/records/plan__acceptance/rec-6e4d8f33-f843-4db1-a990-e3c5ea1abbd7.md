---
{
  "id": "rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Green SHA must be equal to or git-descendant of red SHA; dirty red accepted only with non-empty diff_sha256",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "red-first",
    "requirement": "R3",
    "verify_command": "uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-10T23:44:06+00:00",
  "relationships": {},
  "revision": "sha256:6f3924b9359c5dbfc9bcc81839cafdc0f08a4bb7f452d5b04e627f128fb21954",
  "subject": "close-red-first-order",
  "time": {
    "as_of": "2026-10-10T23:44:06+00:00"
  }
}
---

