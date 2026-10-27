---
{
  "id": "rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Dashboard suite chrome + verify-budget + skill-contract consistency green; red-first for tdd unchanged",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "verification-policy",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k suite && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-15T08:46:11+00:00",
  "relationships": {},
  "revision": "sha256:213f674e700d8a5674883da293d6037b763b76e5b32a7edc4caee65986bb8c8d",
  "subject": "verify-verification-policy-surfaces",
  "time": {
    "as_of": "2026-10-15T08:46:11+00:00"
  }
}
---

