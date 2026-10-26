---
{
  "id": "rec-34f5bd84-dee8-4fa6-bf3a-1f646de23f5e",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "execute-phase documents a commit per task on the phase branch before verify, and the dedicated tests for that rule pass",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "check-runner",
    "requirement": "R6",
    "verify_command": "uv run --with pytest python -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_skill_contract_consistency.py -q -k 'commit or landing or task_commit'"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-10T21:55:13+00:00",
  "relationships": {},
  "revision": "sha256:ae5b43d91ae0fd8f18cf94c8b72cf18e0e054f92c94d7d061c5b83033e6c976f",
  "subject": "task-commit",
  "time": {
    "as_of": "2026-10-10T21:55:13+00:00"
  }
}
---

