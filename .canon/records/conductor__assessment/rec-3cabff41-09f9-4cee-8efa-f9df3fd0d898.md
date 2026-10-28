---
{
  "id": "rec-3cabff41-09f9-4cee-8efa-f9df3fd0d898",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "package-layout",
    "missing": "",
    "next": "release",
    "phase": "wheel-contents",
    "requirement": "R12",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T07:52:29+00:00",
  "relationships": {},
  "revision": "sha256:5214a4dc8cb57e592c500fa0cb7b1b512ae47fc8d83527c48e5f829f0c74c51d",
  "subject": "wheel-contents-R12"
}
---

## Evidence

Green check-run rec-6e34a3ef-2528-4f43-8660-fdfe6ef6c33a result pass at b6245f5bd3c7cb835c96d231cf31dea308bb6a2b. Assertion-level red check-run rec-4bc29cfe-3721-4ab6-ab43-d5281ee63769 result fail revision dirty. Frozen oracle tests/test_wheel_contents.py:sha256:27870adc050644f052b4d272c41b4693ee9e2b52966bbdb94cd4ff7f16d260fd was not edited.

## Missing

none

## Reason

The check for R12 passed on the sessions-package commit, so the requirement holds.
