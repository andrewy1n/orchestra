---
{
  "id": "rec-20f81a2f-2df9-4e5d-9eec-63da3defeec3",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "check and manual done closes succeed without red_check_run_id",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "red-first",
    "requirement": "R5",
    "verify_command": "uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_other_methods"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-10T23:44:06+00:00",
  "relationships": {},
  "revision": "sha256:9801e5bd2debae1e7c6d673ab42a0053d560e6613409d7c4be01efbff5ec0aa6",
  "subject": "close-red-first-methods",
  "time": {
    "as_of": "2026-10-10T23:44:06+00:00"
  }
}
---

