---
{
  "id": "rec-17c17312-7c0a-4faa-9fca-cf2154ee3b5f",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "one line per record",
    "choice": "Activity merges consecutive items of the same kind and outcome into one line naming their subjects",
    "effort": "dashboard",
    "phase": "phase-selector"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-05T07:34:08+00:00",
  "relationships": {},
  "revision": "sha256:2a8f33f485508ff29b26de8f4fd34993cf154de5349a571adc217d73808428e3",
  "subject": "activity-merge",
  "time": {
    "as_of": "2026-10-05T07:34:08+00:00"
  }
}
---

## Rationale

The user chose this. Runs like five `insufficient → verify` assessments are one fact; merging frees lines for distinct events.

## Counter-argument

One line per record keeps each line's time exact and maps one line to one record, which is easier to trust and test.
