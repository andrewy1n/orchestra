---
{
  "id": "rec-e73cbcef-26ef-49b9-8600-e28baca9d0a5",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "verify-exec",
    "depends_on": [
      "phase-sections"
    ],
    "effort": "dashboard-ui",
    "kind": "deliver",
    "phase": "task-navigation",
    "title": "Integration-test task navigation and verify the phase"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-01T22:18:20+00:00",
  "relationships": {},
  "revision": "sha256:6a3e3f791b4f70610e1e9f1becee98d2fa57baaa87c7bffb93fdbb2dfef15e60",
  "subject": "verify-task-navigation-phase"
}
---

## Description

In the isolated tmux popup, drive tabs, phase sections, a phase detail, and a task below the first row with keys only; run the full suite; then get the user's sign-off. Waits on phase-sections.
