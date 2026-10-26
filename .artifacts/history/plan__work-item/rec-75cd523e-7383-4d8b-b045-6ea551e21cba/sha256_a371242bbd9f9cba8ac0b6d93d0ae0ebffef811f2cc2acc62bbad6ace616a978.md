---
{
  "id": "rec-75cd523e-7383-4d8b-b045-6ea551e21cba",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "parent",
    "depends_on": [
      "package-move",
      "package-install",
      "task-table-module",
      "task-detail-module"
    ],
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "dashboard-package",
    "title": "Verify Move the dashboard code out of scripts"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T19:18:21+00:00",
  "relationships": {},
  "revision": "sha256:a371242bbd9f9cba8ac0b6d93d0ae0ebffef811f2cc2acc62bbad6ace616a978",
  "subject": "verify-dashboard-package"
}
---

## Description

Prove the phase exit criteria hold together: run the launcher end to end and the tmux tests, then every other phase check.
