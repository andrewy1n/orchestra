---
{
  "id": "rec-7154f69a-d9d6-4e79-9590-e17f2113bca6",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "suite-dashboard",
    "decisions": [
      "phase-gate-shape"
    ],
    "depends_on": [
      "phase-gate-contract"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 12,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "verification-policy",
    "requirements": [
      "R5"
    ],
    "size": "M",
    "title": "Dashboard suite status chrome"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-15T09:00:27+00:00",
  "relationships": {},
  "revision": "sha256:afc04aff8e19de1d888ded98040990fa8dc8de5fa6be4cbd453edb01ff9f82f2",
  "subject": "suite-dashboard"
}
---

## Description

Show phase-end suite status on the phase header using `<phase>-suite` (not `-tier2`).

## Approach

1. Update `dashboard/model.py` suite/tier2 helpers to look up subject `<phase>-suite` (optional short-lived read of legacy `-tier2` for display only).
2. Rename user-visible labels from tier-2 / t2 to suite / suite status as appropriate.
3. Cover with model + pilot tests (`-k suite` or updated `-k tier2` renamed).
4. Do not edit `skills/` or the suite runner (owned by suite-engine).
