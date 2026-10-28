---
{
  "id": "rec-7ae9ccae-419f-43df-9773-3d8de225e4ef",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "package-layout",
    "missing": "",
    "next": "release",
    "phase": "wheel-contents",
    "requirement": "R1",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T07:47:24+00:00",
  "relationships": {},
  "revision": "sha256:1027d3f1655743f7c5a559259dd47822c05e7a19b3cd072d8b9dfd691fdd6406",
  "subject": "wheel-contents-R1"
}
---

## Evidence

Green check-run rec-95f1dbfb-6083-4224-b263-bb45f13f0203 result pass at ba0783bb8e0138ed83b71ca38f3e0437fb5ffc55. Assertion-level red check-run rec-c98ed94e-af30-43b6-b14c-3a8aa0aa61a9 result fail revision dirty. Frozen oracle tests/test_wheel_contents.py:sha256:27870adc050644f052b4d272c41b4693ee9e2b52966bbdb94cd4ff7f16d260fd was not edited.

## Missing

none

## Reason

The check for R1 passed on the task commit, so the requirement holds.
