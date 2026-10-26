---
{
  "id": "rec-910eed74-aa0f-4d5f-af8b-aa7323cf0f9a",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "test_estimate_view_blank_executor fails before the change and passes after: a task with no size and no estimate_minutes still has executor subagent, an empty size, and no minutes.",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "estimate-view",
    "requirement": "R7",
    "verify_command": "uv run --with pytest python -m pytest tests/test_dashboard_model.py -q -k estimate_view_blank_executor"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-05T06:20:57+00:00",
  "relationships": {},
  "revision": "sha256:02d1034361e5e3477589dc51d9e870b81fb11f2018286b8f0f4bc0b8b3ca2fb7",
  "subject": "estimate-model-blank",
  "time": {
    "as_of": "2026-10-05T06:20:57+00:00"
  }
}
---

