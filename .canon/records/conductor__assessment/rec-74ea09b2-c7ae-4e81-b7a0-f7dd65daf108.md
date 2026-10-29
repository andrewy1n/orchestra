---
{
  "id": "rec-74ea09b2-c7ae-4e81-b7a0-f7dd65daf108",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "ci",
    "missing": "",
    "next": "release",
    "phase": "wheel-smoke",
    "requirement": "R20",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-29T09:32:25+00:00",
  "relationships": {},
  "revision": "sha256:10b6ee796c07dd596b56afc9a6b1a91d950bf970357423bf7dfd6a99c9e3e60b",
  "subject": "wheel-smoke-R20"
}
---

## Evidence

Assertion-level red check-run rec-3c52e566-a2d1-4ddc-a86c-7a001e0299c2 result=fail revision=dirty diff_sha256 present. Green check-run rec-1e793d9a-ae48-4442-9607-6f9b7972595d result=pass at 645bdd9d4563d481cb3c085f024b183e0256e5e2. Frozen oracle hash matched: tests/test_wheel_smoke.py:sha256:7b2d294d69a80da4963e22022debc06efcc860b032e405c04ceb663fd91709ee.

## Missing

none

## Reason

The script leaves the checkout git status unchanged.
