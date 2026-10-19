---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-6e4d8f33-f843-4db1-a990-e3c5ea1abbd7",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Green SHA must be equal to or git-descendant of red SHA; dirty red accepted only with non-empty diff_sha256",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "red-first",
    "requirement": "R3",
    "verify_command": "uv run --with pytest python -m pytest tests/test_close_batch.py -q -k red_first_order"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-10T23:44:06+00:00",
  "relationships": {},
  "revision": "sha256:63d16794907b3587af28fa39f282306ccffa4b9ff60c96ddea7060e4e1166a86",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "close-red-first-order",
  "time": {
    "as_of": "2026-10-10T23:44:06+00:00"
  }
}
---

