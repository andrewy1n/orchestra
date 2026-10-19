---
{
  "base_kind": "task",
  "id": "rec-866d19de-9eca-443d-bc24-17cb15dbcdc4",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "web-ui-detail",
    "decisions": "web-dashboard-toolchain,web-dashboard-styling",
    "effort": "dashboard",
    "estimate_minutes": 18,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "web-dashboard",
    "requirements": "R14,R15,R16,R17,R18,R19",
    "size": "L",
    "title": "Open phase, task, requirement, record, and item details"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-19T07:43:15+00:00",
  "relationships": {
    "depends_on": [
      "rec-a6a8056f-9dee-4efb-a387-c15e653a75be"
    ]
  },
  "revision": "sha256:fa4a455af46f9fd08a394d6ae57e11a0da01e114194e041ecb5906f98f42cb07",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "web-ui-detail"
}
---

## Description

R14: Opening a phase shows the payload of GET /api/phase, including the tabs dashboard.model.tabs_for returns for that phase.
R15: Opening a task shows the payload of GET /api/task.
R16: Opening a requirement shows the payload of GET /api/requirement.
R17: Opening a record shows the payload of GET /api/record.
R18: Opening a Needs you item shows the payload of GET /api/needs.
R19: Opening a backlog item shows the payload of GET /api/backlog.

## Approach

- Hash routes open overlays for a phase, task, requirement, record, Needs you item, and backlog item.
- Each overlay renders the payload of the matching GET route. The phase overlay includes the tabs `tabs_for` returned.
- Make the R14 through R19 cases in `dashboard/web/ui/src/detail.test.ts` pass.
