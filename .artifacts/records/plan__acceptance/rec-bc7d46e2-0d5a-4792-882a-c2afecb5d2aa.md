---
{
  "id": "rec-bc7d46e2-0d5a-4792-882a-c2afecb5d2aa",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "? shows the keys available on the current screen and focused widget",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "phase-selector",
    "requirement": "R12",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'help or question'"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-05T17:38:55+00:00",
  "relationships": {},
  "revision": "sha256:ee52c800d808c20327ecd8a1e6ede1e55fdee37ab4340c5e3a3a17d07e758afd",
  "subject": "phase-selector-ui-help",
  "time": {
    "as_of": "2026-10-05T17:38:55+00:00"
  }
}
---

