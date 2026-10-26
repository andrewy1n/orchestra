---
{
  "id": "rec-fc29e6a5-b457-4d7b-adba-cd4f765a74a7",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "waits-on-compact",
    "requirement": "R3",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-10T08:31:41+00:00",
  "relationships": {},
  "revision": "sha256:5ca3b9d680d20a69ac279dca95a737a485e89fe8e4b0734724b4587b2f70883e",
  "subject": "waits-on-compact-R3",
  "time": {
    "as_of": "2026-10-10T08:31:41+00:00"
  }
}
---

## Evidence

App pilot waiting_row at 60/120: no waits on, no newline in title cell with several unfinished deps.

## Missing

none

## Reason

All check-runs for R3 passed after the title_cell change; the requirement holds.
