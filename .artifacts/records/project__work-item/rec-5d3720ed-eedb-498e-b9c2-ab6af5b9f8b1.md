---
{
  "base_kind": "task",
  "id": "rec-5d3720ed-eedb-498e-b9c2-ab6af5b9f8b1",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "web-ui-actions",
    "decisions": "web-dashboard-writes,web-dashboard-toolchain",
    "effort": "dashboard",
    "estimate_minutes": 14,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "web-dashboard",
    "requirements": "R20,R27",
    "size": "M",
    "title": "Confirm writes and show dismiss errors"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-19T07:59:18+00:00",
  "relationships": {
    "depends_on": [
      "rec-866d19de-9eca-443d-bc24-17cb15dbcdc4",
      "rec-4474072a-2ef4-487a-afd8-73d4482094c2"
    ]
  },
  "revision": "sha256:50ab833c17f8bd2d85051a367c4da3206c7ea4221d4f71dd013b6b5ebd8a5f22",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "web-ui-actions"
}
---

## Description

R20: The page asks for confirmation before it sends a store write.
R27: When dismiss_item raises, the page shows that error.

## Approach

- A confirm control is required before POST `/api/needs` or POST `/api/backlog`. Reject and accept keep the note field the API already requires.
- When the write response is an error from `dismiss_item`, show that error on the page.
- Make the R20 and R27 cases in `dashboard/web/ui/src/actions.test.ts` pass.
