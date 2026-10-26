---
{
  "id": "rec-83de6256-c7b4-4cba-8579-d7cf0edfe73f",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Always render the graph",
    "choice": "Omit the graph when the phase has two or fewer tasks; show chips or wave strip only",
    "effort": "dashboard",
    "phase": "task-graph"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-20T03:10:52+00:00",
  "relationships": {},
  "revision": "sha256:bce13e733fe021a0d55180a320bab2ec7b08aebf0512024c45a6d46558d5f07a",
  "subject": "task-graph-tiny-skip",
  "time": {
    "as_of": "2026-10-20T03:10:52+00:00"
  }
}
---

## Rationale

One or two tasks do not need a graph; chips or the wave strip suffice and avoid empty chrome.

## Counter-argument

Always showing the graph keeps the layout consistent. That was rejected as visual noise for trivial phases.
