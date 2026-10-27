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
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-10T21:55:13+00:00",
  "relationships": {},
  "revision": "sha256:10c364b594189a8b78066e11eeecf6d8034745a434c9655d2a9fd7ead88d2080",
  "subject": "task-commit",
  "time": {
    "as_of": "2026-10-10T21:55:13+00:00"
  }
}
---

