---
{
  "id": "rec-5acd72b1-7099-4efa-a8b1-ac7f5c99ebd1",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "When the CLI rejects a stale expected-revision, dismiss raises a clear error and does not retry with @current",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "dashboard-approvals",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale'"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-11T21:12:47+00:00",
  "relationships": {},
  "revision": "sha256:bbd3eaaf3bcc0898bc4ffef478888ebe6394cc7b32dcd84357494f7d9af87481",
  "subject": "approval-dismiss-stale",
  "time": {
    "as_of": "2026-10-11T21:12:47+00:00"
  }
}
---

