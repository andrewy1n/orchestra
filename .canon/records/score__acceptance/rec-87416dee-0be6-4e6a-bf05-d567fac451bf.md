---
{
  "id": "rec-87416dee-0be6-4e6a-bf05-d567fac451bf",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Integration-report body is filled from the reviewer integration section; skill/contract consistency stays green",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "phase-reviewer",
    "requirement": "R6",
    "verify_command": "uv run --with pytest python -m pytest tests/test_phase_reviewer.py tests/test_skill_contract_consistency.py -q -k \"integration or test_skill_contract\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-11T06:40:02+00:00",
  "relationships": {},
  "revision": "sha256:2f26a896df3f399e22ab2cc3dcfe64b15cda865e5c40e2a634bcd3bdc385289b",
  "subject": "reviewer-execute-integration",
  "time": {
    "as_of": "2026-10-11T06:40:02+00:00"
  }
}
---

