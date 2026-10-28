---
{
  "id": "rec-7ca96db0-917f-4546-a33f-c51c3fdcdda2",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "package-layout",
    "missing": "",
    "next": "release",
    "phase": "wheel-contents",
    "requirement": "R3",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T07:47:16+00:00",
  "relationships": {},
  "revision": "sha256:c1f1de9588279215bc902fc6bf1a344e249685c73e654a00f9dfd25556f815a7",
  "subject": "wheel-contents-R3"
}
---

## Evidence

Green check-run rec-22610849-9909-4ffd-8604-a1dc2a859c90 result pass at ba0783bb8e0138ed83b71ca38f3e0437fb5ffc55. Assertion-level red check-run rec-4ccccefb-2aa2-484a-84c0-b9dbf367ed2b result fail revision dirty. Frozen oracle tests/test_wheel_contents.py:sha256:27870adc050644f052b4d272c41b4693ee9e2b52966bbdb94cd4ff7f16d260fd was not edited.

## Missing

none

## Reason

The check for R3 passed on the task commit, so the requirement holds.
