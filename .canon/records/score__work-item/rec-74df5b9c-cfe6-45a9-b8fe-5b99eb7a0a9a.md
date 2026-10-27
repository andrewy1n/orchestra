---
{
  "id": "rec-74df5b9c-cfe6-45a9-b8fe-5b99eb7a0a9a",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-verify-needs-you-phase",
    "depends_on": [
      "needs-you-list",
      "finished-effort-view"
    ],
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "features-needs-you",
    "title": "Integration-test Needs you and finished efforts and verify the phase"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T03:16:23+00:00",
  "relationships": {},
  "revision": "sha256:d21184bac8fca74d49f96fd7163d8472fee18bfcab09820a5e1fa00be21e554f",
  "subject": "verify-needs-you-phase"
}
---

## Description

Add a tmux popup test that presses n, walks the list, opens a task-linked item and a question, returns with esc, and sees a finished effort sorted last with All N tasks done. Update README keys and screens. Run the full suite. Waits on needs-you-list and finished-effort-view.
