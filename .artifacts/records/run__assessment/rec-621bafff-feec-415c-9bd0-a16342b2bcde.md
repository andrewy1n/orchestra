---
{
  "id": "rec-621bafff-feec-415c-9bd0-a16342b2bcde",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "phase-selector",
    "requirement": "R7",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-05T20:50:45+00:00",
  "relationships": {},
  "revision": "sha256:c11687530de8960a5db5f7d19c992161cf8d9c73bb26545fcc3d67b9800c2468",
  "subject": "phase-selector-R7",
  "time": {
    "as_of": "2026-10-05T20:50:45+00:00"
  }
}
---

## Evidence

Check-run rec-c5cfe635-9a9b-4497-8f2b-5c5bfb4588e3 passed. `tests/test_dashboard_model.py -k 'follow or pin'` passed 4. Selection follows the default until a different phase is picked, stays pinned, and resumes following when the current default is picked again.

## Missing

none

## Reason

Follow, pin, resume, and missing-phase fallback are covered by the passing unit checks.
