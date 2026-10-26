---
{
  "id": "rec-7051d521-de6d-4e4d-9eb1-acf5c73bb6df",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "deep-links",
    "requirement": "R8",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-20T04:39:41+00:00",
  "relationships": {},
  "revision": "sha256:42f1a01485dd53df1a4f468d0c1118e4a9a99203cec45bd876d36b5538c35bf6",
  "subject": "deep-links-R8",
  "time": {
    "as_of": "2026-10-20T04:39:41+00:00"
  }
}
---

## Evidence

check-run rec-86c42115-690b-4b07-8f6e-2c9346721449 pass at 3216e017 (vitest links.test.ts -t R8)

## Missing

none

## Reason

The resolve helper satisfies R8 at the cited revision; the focused check passed.
