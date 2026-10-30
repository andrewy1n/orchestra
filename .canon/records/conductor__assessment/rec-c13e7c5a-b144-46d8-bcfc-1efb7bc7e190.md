---
{
  "id": "rec-c13e7c5a-b144-46d8-bcfc-1efb7bc7e190",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "high",
    "effort": "ci",
    "missing": "",
    "next": "release",
    "phase": "ci-workflow",
    "requirement": "R28",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-29T05:58:04+00:00",
  "relationships": {
    "supersedes": [
      "rec-c5722673-2a99-452f-b210-53f9138c4d90"
    ]
  },
  "revision": "sha256:e165c8bc855d8a143808b7c8d52f4cc726f44c75b3288ce6f3886e40f53727cc",
  "subject": "ci-workflow-R28"
}
---

## Evidence

Verification check-run rec-974c1a62-73c2-461a-bc65-95d930b728c6 passed at 2835bd8049daef46fec360ac67c4a73bcfe141a6: scripts/test.sh is absent and no tracked file references it. Earlier task-level check-runs for this requirement also passed.

## Missing

none

## Reason

The acceptance command exercises the requirement directly and passed.
