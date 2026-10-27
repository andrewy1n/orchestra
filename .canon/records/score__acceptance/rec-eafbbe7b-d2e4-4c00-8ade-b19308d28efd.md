---
{
  "id": "rec-eafbbe7b-d2e4-4c00-8ade-b19308d28efd",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "A Needs you item absent from the previous snapshot rings the bell and shows a stubbed tmux message naming effort, action, and subject; items present at startup do not alert",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "human-gates",
    "requirement": "R9",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k \"gates and (alert or bell or message)\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-09T20:44:01+00:00",
  "relationships": {},
  "revision": "sha256:7b10841455c5077f6ff754c8a5ab0bcad0ff28f2a181e44ef4f6c6531839cb71",
  "subject": "gates-ui-alert",
  "time": {
    "as_of": "2026-10-09T20:44:01+00:00"
  }
}
---

