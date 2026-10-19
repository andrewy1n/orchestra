---
{
  "base_kind": "task",
  "id": "rec-a6a8056f-9dee-4efb-a387-c15e653a75be",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "web-ui-side",
    "decisions": "web-dashboard-toolchain,web-dashboard-styling",
    "effort": "dashboard",
    "estimate_minutes": 12,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "web-dashboard",
    "requirements": "R11,R12,R13",
    "size": "M",
    "title": "Show Needs you, journal, and backlog"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-19T07:39:54+00:00",
  "relationships": {
    "depends_on": [
      "rec-7102f038-1cb1-4752-99f1-2ed73eec9f25"
    ]
  },
  "revision": "sha256:4cf9a56bcd51a5b0c0528f710d31fa718000eeb19bf9fb737595bf4eb3f8acef",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "web-ui-side"
}
---

## Description

R11: The side column lists the selected effort's Needs you items.
R12: The side column lists the selected effort's journal in dashboard.journal.ordered order, each row showing the record type and subject.
R13: The side column lists the selected effort's open backlog items.

## Approach

- The side column lists the selected effort's Needs you items, its journal, and its open backlog items.
- Journal rows come from GET `/api/journal` in `dashboard.journal.ordered` order and show the record type and subject.
- Make the R11, R12, and R13 cases in `dashboard/web/ui/src/side.test.ts` pass.
