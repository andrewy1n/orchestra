---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-0e593cda-ace5-410a-b548-a5ab4c5c18fd",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Dashboard suite chrome + verify-budget + skill-contract consistency green; red-first for tdd unchanged",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "verification-policy",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k suite && uv run --with pytest python -m pytest tests/test_verify_budget.py tests/test_skill_contract_consistency.py -q"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-15T08:46:11+00:00",
  "relationships": {},
  "revision": "sha256:2a60bf4b834fd73738e3931d7b33cf4463eb86cd390a7d058b2ea93d0fc2aafe",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verify-verification-policy-surfaces",
  "time": {
    "as_of": "2026-10-15T08:46:11+00:00"
  }
}
---

