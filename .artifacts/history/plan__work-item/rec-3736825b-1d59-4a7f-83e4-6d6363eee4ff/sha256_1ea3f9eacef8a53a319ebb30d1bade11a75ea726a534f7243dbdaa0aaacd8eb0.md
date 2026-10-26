---
{
  "id": "rec-3736825b-1d59-4a7f-83e4-6d6363eee4ff",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-tmux-scripts",
    "effort": "watch-dashboard",
    "kind": "deliver",
    "phase": "tmux-integration",
    "title": "Print a one-line dashboard summary for the status line"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-09-29T23:23:46+00:00",
  "relationships": {},
  "revision": "sha256:1ea3f9eacef8a53a319ebb30d1bade11a75ea726a534f7243dbdaa0aaacd8eb0",
  "subject": "dashboard-status-segment"
}
---

## Description

Add ~/se-workflow/scripts/dashboard-status. It reads Claude Code status JSON on stdin (workspace.current_dir, else cwd) or a directory argument, resolves the store like scripts/dashboard, and prints one line per live effort focus such as: watch-dashboard · 1 running · 2 ready · 1 needs you. It prints nothing when there is no store or no dashboard view. Add a README note on appending it to an existing status line script.
