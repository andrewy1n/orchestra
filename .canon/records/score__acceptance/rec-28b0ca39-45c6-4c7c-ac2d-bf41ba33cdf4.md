---
{
  "id": "rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "bin/se-workflow exists, sync-plugin copies bin and se_workflow, and README documents the entry point",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "check-runner",
    "requirement": "R8",
    "verify_command": "uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k \"entry or sync or install or bin\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-10T21:55:21+00:00",
  "relationships": {},
  "revision": "sha256:00edd2dfec01bcd1d7f986ad1b30f320e3fc9ff416c291936c4202298a38e44e",
  "subject": "se-workflow-check-entry",
  "time": {
    "as_of": "2026-10-10T21:55:21+00:00"
  }
}
---

