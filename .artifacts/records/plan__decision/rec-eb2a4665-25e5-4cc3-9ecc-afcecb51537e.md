---
{
  "id": "rec-eb2a4665-25e5-4cc3-9ecc-afcecb51537e",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Allow repo-wide unassigned backlog items",
    "choice": "payload.effort required on every backlog-item",
    "effort": "workflow-loop",
    "phase": "backlog-capture"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-10T09:06:51+00:00",
  "relationships": {},
  "revision": "sha256:8af0cd97f9cb9ebd32dd53cdc2ef165923dd420ee19e9601f82c012050895bf4",
  "subject": "backlog-effort-scope",
  "time": {
    "as_of": "2026-10-10T09:06:51+00:00"
  }
}
---

## Rationale

Every other task-scoped and effort-scoped record in se-workflow hangs off a goal subject. Promotion into a phase or incidental work-item needs an effort anyway. Requiring `payload.effort` keeps handoff grouping and reopen rules simple and avoids orphan items with no product area.

## Counter-argument

Repo-wide unassigned items would let agents park ideas before an effort exists. The cost is a second indexing path (not under any goal), weaker handoff sections, and a later obligatory "assign effort" step that reopens the same design question.
