---
{
  "id": "rec-c05df7eb-a2fe-4be4-afee-86d2a818751b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "a flat task list with a phase column on All phases",
    "choice": "Collapsible phase sections, with older done phases folded, appear only on the All phases stop; a selected phase lists its tasks with no header rows",
    "effort": "dashboard",
    "phase": "phase-selector"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-05T07:34:08+00:00",
  "relationships": {
    "supersedes": [
      "rec-ec078b21-77e1-4dbe-9ae4-8282cf8cbb62"
    ]
  },
  "revision": "sha256:7e0ce3551bbb778a32968fd97be6499c14091dd696068c351d0eab707b97dd16",
  "subject": "phase-sections",
  "time": {
    "as_of": "2026-10-05T07:34:08+00:00"
  }
}
---

## Rationale

The user chose to keep the grouped table for All phases. With a phase selected, header rows add nothing, and every row opening a task removes the three meanings Enter had.

## Counter-argument

A flat list with a phase column is one row type everywhere, so the cursor and Enter behave the same on every stop.
