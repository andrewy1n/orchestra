---
{
  "id": "rec-e2554cac-2147-4a3f-bebf-8d6d51adbb8a",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-verify-needs-you-data-phase",
    "depends_on": [
      "needs-you-tab-removal",
      "unsigned-check-label"
    ],
    "effort": "dashboard",
    "kind": "repair",
    "phase": "bugfix-needs-you-data",
    "title": "Integration-test the needs-you data fixes and verify the phase"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T03:16:22+00:00",
  "relationships": {},
  "revision": "sha256:c9b452de57a04923d7ca0d7a446fd5aed63c2cc8657cf499b7ec47ed6820b186",
  "subject": "verify-needs-you-data-phase"
}
---

## Description

Update the tmux popup tests to walk six tabs and see the counted panel title and a readable unsigned-check line. Run the full suite. Waits on needs-you-tab-removal and unsigned-check-label.
