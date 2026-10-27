---
{
  "id": "rec-b147b60a-bac3-473f-bff5-6ea8db7fe2e9",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "plan-phase writes verification acceptances from the phase exit criteria, including one integration check through the real entry point",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "verify-budget",
    "requirement": "R1",
    "verify_command": "uv run --with pytest python -m pytest tests/test_verify_budget.py -q -k plan_phase_limits"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-09T22:37:53+00:00",
  "relationships": {},
  "revision": "sha256:e2daa644f65ea2962c3ae6b6fb4d488a410c1a94975f9f2f3e5a2ded75837486",
  "subject": "budget-instructions",
  "time": {
    "as_of": "2026-10-09T22:37:53+00:00"
  }
}
---

