---
{
  "id": "rec-e2d0fbad-e656-4ae7-bdc8-5085a4d28e84",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "package-layout",
    "missing": "",
    "next": "release",
    "phase": "wheel-contents",
    "requirement": "R28",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T07:55:40+00:00",
  "relationships": {},
  "revision": "sha256:97773938078c5aab4a3af1481c2887bf2b9805d42141b4caacfe9bd8bb97c9ec",
  "subject": "wheel-contents-R28"
}
---

## Evidence

Green check-run rec-bc033e06-5170-46fc-b55b-a2a9f5e05c32 result pass at 268a9d35e9700bd01264a01404b2d7d0489a6046. tests/test_cli_packaging.py and tests/integration/test_declared_install.py passed after the fixtures copied dashboard and installer.

## Missing

none

## Reason

The install fixtures can build the wheel, so R28 holds.
