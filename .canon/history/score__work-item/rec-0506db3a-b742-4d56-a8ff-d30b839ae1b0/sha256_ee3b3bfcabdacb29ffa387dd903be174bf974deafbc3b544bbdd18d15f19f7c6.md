---
{
  "id": "rec-0506db3a-b742-4d56-a8ff-d30b839ae1b0",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "parent",
    "depends_on": [
      "status-line-from-snapshot"
    ],
    "effort": "dashboard-bugfix",
    "kind": "repair",
    "phase": "bugfix-status-line",
    "title": "Integration-test the status line and verify the phase"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T00:11:11+00:00",
  "relationships": {},
  "revision": "sha256:ee3b3bfcabdacb29ffa387dd903be174bf974deafbc3b544bbdd18d15f19f7c6",
  "subject": "verify-status-line-phase"
}
---

## Description

Run the tmux status segment test and the e2e side-pane test against the rebuilt status line, update README if its description changes, and run the full suite. Waits on status-line-from-snapshot.
