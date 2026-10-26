---
{
  "id": "rec-dd4fcd94-68f4-47e2-aa6d-f86998cf25fd",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-e2e-scripted-run",
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "end-to-end-verification",
    "title": "Drive the full dashboard chain in one scripted test"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T03:16:20+00:00",
  "relationships": {},
  "revision": "sha256:d93a4aef6c81b451f63b82ecd9687fdfbb6358a344989c582716ba6a5a56fe86",
  "subject": "e2e-scripted-run"
}
---

## Description

Add ~/se-workflow/tests/test_e2e_dashboard.py. Scratch repo adopted through the CLI; goal, phase, work-items a, b (depends on a), c (depends on b). Isolated tmux server with the conf and a pty client; prefix + S opens the side pane running watch. Steps: a in_progress, a done, blocking question added, question answered, b in_progress, b done. After each step wait for the side pane to redraw and check the full section map; check the dashboard-status line.
