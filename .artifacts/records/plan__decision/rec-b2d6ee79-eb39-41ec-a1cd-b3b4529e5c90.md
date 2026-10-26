---
{
  "id": "rec-b2d6ee79-eb39-41ec-a1cd-b3b4529e5c90",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Include check-runs and execution reports for context",
    "choice": "Specs, acceptances, invariants, and phase diff only; no builder self-grades",
    "effort": "workflow-loop",
    "phase": "phase-reviewer"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-11T06:26:05+00:00",
  "relationships": {},
  "revision": "sha256:c9281a5dba9e7b67808c74b9c9e0114fcf0b48d70082527d0f5e5a6df4158502",
  "subject": "reviewer-inputs",
  "time": {
    "as_of": "2026-10-11T06:26:05+00:00"
  }
}
---

## Rationale

Harness practice and the `status-tabs` escape show that grading from the builder's own reports anchors on a pass that missed the description. Limiting inputs to specs, acceptances, invariants, and the phase diff forces the reviewer to compare intent to the tree. The parent still records evidence so the single-writer rule holds.

## Counter-argument

Giving the reviewer check-runs and execution reports would reduce false NEEDS_WORK when a behavior is already proven by tests. The cost is reintroducing builder-anchored grading and missing description gaps that never made it into acceptances.
