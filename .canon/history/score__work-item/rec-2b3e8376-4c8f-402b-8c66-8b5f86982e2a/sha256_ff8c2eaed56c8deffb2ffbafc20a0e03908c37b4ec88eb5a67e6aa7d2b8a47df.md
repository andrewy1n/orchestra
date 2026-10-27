---
{
  "id": "rec-2b3e8376-4c8f-402b-8c66-8b5f86982e2a",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "sub-dashboard-launcher-switch",
    "depends_on": [
      "dashboard-app"
    ],
    "effort": "dashboard-ui",
    "kind": "deliver",
    "phase": "readable-layout",
    "title": "Launch the Textual dashboard from scripts/dashboard"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-09-30T19:12:07+00:00",
  "relationships": {},
  "revision": "sha256:ff8c2eaed56c8deffb2ffbafc20a0e03908c37b4ec88eb5a67e6aa7d2b8a47df",
  "subject": "dashboard-launcher-switch"
}
---

## Description

`scripts/dashboard` runs the Textual app through uv. The no-store message stays. It no longer requires the `project:dashboard` view. Update the launcher and tmux tests and the README. `dashboard-status` is unchanged. Waits on the app.
