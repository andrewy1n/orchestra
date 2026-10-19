---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-84aa203e-910a-40ea-a99b-1e0c3efdda28",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Stale displayed revision shows a visible message and skips the write; no @current retry",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "dashboard-approvals",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale'"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-11T21:12:58+00:00",
  "relationships": {},
  "revision": "sha256:4ff2eb229cff5ea6c754133eb3e32cc73e102e22f97744434b65dd1311ed544d",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verify-dashboard-approvals-revision",
  "time": {
    "as_of": "2026-10-11T21:12:58+00:00"
  }
}
---

