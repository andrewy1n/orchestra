---
{
  "id": "rec-d2f45e59-d643-45ff-97f9-72e4edd0debb",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Task detail for a blocked/waiting task still lists Depends on links for its dependencies after the row note is gone; regression holds",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "waits-on-compact",
    "requirement": "R2",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'detail and (Depends or blocked or waiting)'"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-10T08:25:45+00:00",
  "relationships": {},
  "revision": "sha256:8c1ef7424367e74e531a463252edcb20eb304653df22efb47a23af2142f1a4a5",
  "subject": "drop-row-waits-on-detail",
  "time": {
    "as_of": "2026-10-10T08:25:45+00:00"
  }
}
---

