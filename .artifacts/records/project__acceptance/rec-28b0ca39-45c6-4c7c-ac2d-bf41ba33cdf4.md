---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-28b0ca39-45c6-4c7c-ac2d-bf41ba33cdf4",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "bin/se-workflow exists, sync-plugin copies bin and se_workflow, and README documents the entry point",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "check-runner",
    "requirement": "R8",
    "verify_command": "uv run --with pytest python -m pytest tests/test_se_workflow_check.py -q -k \"entry or sync or install or bin\""
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-10T21:55:21+00:00",
  "relationships": {},
  "revision": "sha256:460ee8a1c7501d6441b7474a43689e290885f2f894336838a1b8af564738a835",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "se-workflow-check-entry",
  "time": {
    "as_of": "2026-10-10T21:55:21+00:00"
  }
}
---

