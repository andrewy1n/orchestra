---
{
  "id": "rec-18fd0fc9-9da2-4cc0-a5e1-a968d60dac73",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "test_estimate_view_row_fields fails before the change and passes after: a phase row carries the sitting phrase and elapsed minutes, and a task row carries size, estimate_minutes, and executor from the work-item.",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "estimate-view",
    "requirement": "R4",
    "verify_command": "uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_row_fields"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-05T06:20:57+00:00",
  "relationships": {},
  "revision": "sha256:c986210b21d680f5a4981dd5b274b3d8e76d7304a0764ef5da914209a7a0ef21",
  "subject": "estimate-model-row",
  "time": {
    "as_of": "2026-10-05T06:20:57+00:00"
  }
}
---

