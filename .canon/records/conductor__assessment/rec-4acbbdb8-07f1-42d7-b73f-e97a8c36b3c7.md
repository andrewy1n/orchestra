---
{
  "id": "rec-4acbbdb8-07f1-42d7-b73f-e97a8c36b3c7",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "package-layout",
    "missing": "",
    "next": "release",
    "phase": "wheel-contents",
    "requirement": "R13",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T07:52:27+00:00",
  "relationships": {},
  "revision": "sha256:e5d658e49899cefda9db1060bbfabf70147c7f74ce757e65794a7460574f056d",
  "subject": "wheel-contents-R13"
}
---

## Evidence

Green check-run rec-ca864df6-8031-4bc6-8c5e-b696e1a46b7a result pass at b6245f5bd3c7cb835c96d231cf31dea308bb6a2b. Assertion-level red check-run rec-f0565cef-855a-438a-a102-56a02406ce7b result fail revision dirty. Frozen oracle tests/test_wheel_contents.py:sha256:27870adc050644f052b4d272c41b4693ee9e2b52966bbdb94cd4ff7f16d260fd was not edited.

## Missing

none

## Reason

The check for R13 passed on the sessions-package commit, so the requirement holds.
