---
{
  "id": "rec-27baaa17-ce05-44aa-9ddd-8aa84e77bbe7",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "workflow-loop",
    "missing": "",
    "next": "release",
    "phase": "retry-loop",
    "requirement": "R9",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-11T06:36:04+00:00",
  "relationships": {},
  "revision": "sha256:40e8e8c0121a93f9cc4c82b56bfb15ca59ff353c3f864e85224154936df4dca3",
  "subject": "retry-loop-R9",
  "time": {
    "as_of": "2026-10-11T06:36:04+00:00"
  }
}
---

## Evidence

Skill and contract consistency suites passed via se-workflow check for verify-retry-loop-contract.

## Missing

none

## Reason

Optional attempts is declared and skill invocations stay contract-legal.
