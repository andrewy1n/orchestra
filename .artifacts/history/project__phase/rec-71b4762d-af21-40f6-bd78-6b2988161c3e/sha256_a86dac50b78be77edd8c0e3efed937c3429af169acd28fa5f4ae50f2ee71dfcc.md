---
{
  "base_kind": "phase",
  "id": "rec-71b4762d-af21-40f6-bd78-6b2988161c3e",
  "identity": "unknown",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "dashboard",
    "milestone": "web-calm",
    "ordinal": 32,
    "title": "Milestone-grouped phase nav"
  },
  "record_type": "project:phase",
  "recorded_at": "2026-10-20T03:04:04+00:00",
  "relationships": {},
  "revision": "sha256:a86dac50b78be77edd8c0e3efed937c3429af169acd28fa5f4ae50f2ee71dfcc",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "milestone-nav"
}
---

## Problem

The web dashboard shows every phase in a flat stepper. Milestone data is already in the snapshot API, but the UI ignores it, so efforts with many phases are hard to scan.

## Approach

Decide at settle-phase (UI shape for grouping and defaults).

## Exit criteria

- With milestones present, the main pane groups phases under milestone headers (title, state, done/total); ungrouped phases are last.
- With no milestones, the prior flat phase control remains.
- Default selection is the current milestone's in-progress phase (existing selection rules), not All phases.
- Finished milestones are collapsed by default and can be expanded.
- Verified by UI tests against a seeded snapshot and a manual look at this repo's web dashboard.
