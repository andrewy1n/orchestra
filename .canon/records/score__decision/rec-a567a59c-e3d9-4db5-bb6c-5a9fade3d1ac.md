---
{
  "id": "rec-a567a59c-e3d9-4db5-bb6c-5a9fade3d1ac",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "a focusable stepper row moved with left and right, with the status tabs moved to other keys; a picker only",
    "choice": "[ and ] step through phases with All phases after the last; P opens a filterable phase picker; selector segments are clickable",
    "effort": "dashboard",
    "phase": "phase-selector"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-05T07:34:07+00:00",
  "relationships": {},
  "revision": "sha256:e6280b1e8cc0dfc584acc94aaef742d2f712a8acb8be39fc0535dc0d179fd2df",
  "subject": "phase-selector-keys",
  "time": {
    "as_of": "2026-10-05T07:34:07+00:00"
  }
}
---

## Rationale

The user chose this. Left and right already move between status tabs, so brackets keep them. Stepping covers the common move to a neighbouring phase, and the picker reaches any of twenty-plus phases without scrolling.

## Counter-argument

A focusable stepper is the most discoverable form: the selector looks like tabs, and arrow keys on tabs are what users try first.
