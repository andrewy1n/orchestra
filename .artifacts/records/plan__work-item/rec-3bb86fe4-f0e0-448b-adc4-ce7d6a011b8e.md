---
{
  "id": "rec-3bb86fe4-f0e0-448b-adc4-ce7d6a011b8e",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-keyboard-focus",
    "effort": "dashboard",
    "kind": "repair",
    "phase": "task-navigation",
    "title": "Move through tasks and Activity with the keyboard"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T03:16:20+00:00",
  "relationships": {},
  "revision": "sha256:da587fa9e1d41fc9abb07799a4c05df78521537eedceaaa666d7229b42a68a98",
  "subject": "keyboard-focus"
}
---

## Description

Focus stays on the effort tab strip, so arrows never move the task cursor, enter always opens the first row, tab is taken by effort switching, and Activity cannot be reached. The task table takes focus on load, on effort switch, and on return from detail; up/down and j/k move rows; PgUp/PgDn/Home/End scroll the effort pane; arrows scroll the detail and commit screens.
