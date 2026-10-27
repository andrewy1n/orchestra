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
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T03:16:20+00:00",
  "relationships": {},
  "revision": "sha256:e26fef0a123cc9273818f8e7dbdcb092a6f34077f1515478373f58408359d42e",
  "subject": "keyboard-focus"
}
---

## Description

Focus stays on the effort tab strip, so arrows never move the task cursor, enter always opens the first row, tab is taken by effort switching, and Activity cannot be reached. The task table takes focus on load, on effort switch, and on return from detail; up/down and j/k move rows; PgUp/PgDn/Home/End scroll the effort pane; arrows scroll the detail and commit screens.
