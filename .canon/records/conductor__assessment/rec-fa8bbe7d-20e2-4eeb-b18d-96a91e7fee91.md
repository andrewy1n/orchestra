---
{
  "id": "rec-fa8bbe7d-20e2-4eeb-b18d-96a91e7fee91",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "high",
    "effort": "ci",
    "missing": "",
    "next": "release",
    "phase": "ci-workflow",
    "requirement": "R15",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-28T21:29:41+00:00",
  "relationships": {},
  "revision": "sha256:26fb880cb9c45f67f2cbb521c99845ba4080ab8455537ee56ffbc8ed601ce4d8",
  "subject": "ci-workflow-R15"
}
---

## Evidence

Check-run rec-ba49aab2-803a-4732-9377-72ce3f9c9062 passed at 1eb08185ff7eec1ebe4a62b02b2a2a25eec6a843: tests/test_ci_workflow.py -k test_r15_ asserts the parsed ci.yml.

## Missing

none

## Reason

The structure test parses the workflow and asserts the requirement directly. It failed on assertion before ci.yml existed and passes now.
