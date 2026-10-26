---
{
  "id": "rec-814fad6a-e6dc-4f41-9ba6-07e14bf823aa",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "level": "",
    "missing": "",
    "next": "release",
    "phase": "evidence-view",
    "requirement": "R2",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-05T06:46:42+00:00",
  "relationships": {
    "supersedes": [
      "rec-bda06719-7d35-4b82-9f30-3535eaca1b8b"
    ]
  },
  "revision": "sha256:76e94b6f4761463e082ff76fcc9c18fad6111af16669ec029403b8152d66f389",
  "subject": "evidence-view-R2",
  "time": {
    "as_of": "2026-10-05T06:46:42+00:00"
  }
}
---

## Evidence

tests/test_dashboard_model.py -q -k evidence passed 8, including the R2 model checks. Check-run rec-571ad7b4-d991-4250-8066-99335077a868 passed.

## Missing

none

## Reason

The evidence model tests pass, so the requirement rows still come from the latest assessment.
