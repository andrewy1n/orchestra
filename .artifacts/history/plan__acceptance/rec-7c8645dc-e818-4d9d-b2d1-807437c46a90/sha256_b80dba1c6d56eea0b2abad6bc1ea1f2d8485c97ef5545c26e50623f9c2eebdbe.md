---
{
  "id": "rec-7c8645dc-e818-4d9d-b2d1-807437c46a90",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Pilot tests: n focuses the list, arrows move, enter opens the task detail for a linked item and the Needs-you detail with full text for a question, esc returns, c copies the subject",
    "effort": "dashboard-features",
    "method": "tdd",
    "phase": "features-needs-you",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k needs_you"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-01T22:55:18+00:00",
  "relationships": {},
  "revision": "sha256:b80dba1c6d56eea0b2abad6bc1ea1f2d8485c97ef5545c26e50623f9c2eebdbe",
  "subject": "needs-you-list",
  "time": {
    "as_of": "2026-10-01T22:55:18+00:00"
  }
}
---

