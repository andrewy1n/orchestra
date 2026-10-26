---
{
  "id": "rec-728cba3e-fedb-4e4c-9280-4076853e6192",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-verify-task-rows-phase",
    "depends_on": [
      "task-row-cells",
      "activity-failures"
    ],
    "effort": "dashboard-features",
    "kind": "deliver",
    "phase": "features-task-rows",
    "title": "Integration-test task rows and activity and verify the phase"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T01:41:55+00:00",
  "relationships": {},
  "revision": "sha256:fea34fa45761d33ff091ee177ddfff8cbda13ad51a468ccd46b1cd7c48b9b5ee",
  "subject": "verify-task-rows-phase"
}
---

## Description

A tmux popup test shows a waits-on note, a running time, no phase column, and a red failed activity line. Update README. Run the full suite with -rf. Waits on task-row-cells and activity-failures.
