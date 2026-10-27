---
{
  "id": "rec-6dfec4b9-ee74-45bc-aa1c-b608f21a7a7b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "everything follows the selected phase, including Needs you and Activity; only the task table follows",
    "choice": "Each effort selects a phase, by default the current one. The task table, status-tab counts, and progress bar follow the selection; Needs you and Activity stay effort-wide",
    "effort": "dashboard",
    "phase": "phase-selector"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-05T07:34:07+00:00",
  "relationships": {},
  "revision": "sha256:48b68e8f3cb9b8c4fdc9570148a3ce9e0e8c30ec25845f0c7d01d9166f59270f",
  "subject": "phase-selection-scope",
  "time": {
    "as_of": "2026-10-05T07:34:07+00:00"
  }
}
---

## Rationale

The user chose this. Scoping the table and its counts removes finished tasks from view and gives the per-phase views a selection to follow. Keeping Needs you and Activity effort-wide means nothing waiting on the user is hidden by a selection.

## Counter-argument

Scoping everything would make the screen consistent: every number on it would describe one phase, and a user would never have to ask which scope a panel uses.
