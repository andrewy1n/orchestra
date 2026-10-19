---
{
  "base_kind": "task",
  "id": "rec-b5b0bd7d-5cdf-44b3-bbd2-11f3ccd326c4",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "tier2-dashboard-worker",
    "decisions": "tiered-verification-scope,tier2-execution",
    "effort": "workflow-loop",
    "estimate_minutes": 30,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "tiered-verification",
    "requirements": "R6",
    "size": "M",
    "title": "Show tier-2 status on phase header"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-11T09:42:48+00:00",
  "relationships": {},
  "revision": "sha256:8b969045d12216fd6bc2bc9a5dcc6321999fd714141693b1c27106ea80b20177",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "tier2-dashboard"
}
---

## Description

The dashboard phase header shows tier-2 status as running, passed, or failed at the phase head SHA, derived from the tier-2 check-run (and an in-flight marker when the background job is still running).

## Approach

1. Extend `dashboard/model.py` to resolve tier-2 status per phase from check-runs (subject/evidence convention agreed with tier2-engine) and optional running state.
2. Render compact status on the phase header in `dashboard/tasks.py` / app at 60 and 120 columns without crowding existing attempt/budget/sitting chrome.
3. Pilot tests in `tests/test_dashboard_app.py` and model tests as needed with `-k tier2` (or `tier_2`).
4. Do not edit `skills/` or `se_workflow/` (owned by tier2-engine).
