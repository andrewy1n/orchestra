---
{
  "id": "rec-6169b8cb-4fe3-460e-b7a4-9162494a1b25",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-copy-and-commit-actions",
    "depends_on": [
      "task-list-filters"
    ],
    "effort": "dashboard-ui",
    "kind": "deliver",
    "phase": "dashboard-actions",
    "title": "Copy a task slug and view its commit"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-09-30T21:48:47+00:00",
  "relationships": {},
  "revision": "sha256:cc9a6b4b51c2b26c82ff65acbe03ccb3e187aac1d4d78dffe63eac0ec9ed401c",
  "subject": "copy-and-commit-actions"
}
---

## Description

`c` copies the selected task's slug to the clipboard with Textual's copy_to_clipboard (OSC 52) from the dashboard and the detail screen, with a short notification. `g` on the detail screen opens a commit screen for the latest revision among the task's execution reports and check-runs: the commit message and `git show --stat` output, run in the repo root. Missing, dirty, or unknown revisions show a clear message instead. Esc returns. Footer and README list the keys. Waits on the filters because both edit the app's bindings.
