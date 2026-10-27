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
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T03:16:22+00:00",
  "relationships": {},
  "revision": "sha256:2c8dc3593ba2db42a8c1b6a3e19bb23279726bae579599b29328a4310a6dc038",
  "subject": "verify-needs-you-data-phase"
}
---

## Description

Update the tmux popup tests to walk six tabs and see the counted panel title and a readable unsigned-check line. Run the full suite. Waits on needs-you-tab-removal and unsigned-check-label.
