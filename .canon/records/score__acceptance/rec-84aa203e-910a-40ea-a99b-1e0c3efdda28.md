---
{
  "id": "rec-84aa203e-910a-40ea-a99b-1e0c3efdda28",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Stale displayed revision shows a visible message and skips the write; no @current retry",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "dashboard-approvals",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale'"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-11T21:12:58+00:00",
  "relationships": {},
  "revision": "sha256:337504a5436e521e805825b2a5d3873846ada4c9a6f62496a63d8a0d1c21be30",
  "subject": "verify-dashboard-approvals-revision",
  "time": {
    "as_of": "2026-10-11T21:12:58+00:00"
  }
}
---

