---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-ea3c18ee-16c1-4af6-ab02-a60ef64d5ace",
  "identity": "unknown",
  "lifecycle_state": "superseded",
  "payload": {
    "criterion": "Retrieed task rows show attempt n/budget; model/app tests with -k attempt pass",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "retry-loop",
    "requirement": "R8",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k attempt"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-11T06:27:49+00:00",
  "relationships": {},
  "revision": "sha256:b142a5eb07dd6f0e8ab65a3fa00b448cc28960f660749a9d267962d874a560f8",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "retry-dashboard",
  "time": {
    "as_of": "2026-10-11T06:27:40+00:00"
  }
}
---

