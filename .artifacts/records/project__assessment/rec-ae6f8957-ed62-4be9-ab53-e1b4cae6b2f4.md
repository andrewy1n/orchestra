---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-ae6f8957-ed62-4be9-ab53-e1b4cae6b2f4",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "packaging",
    "missing": "",
    "next": "release",
    "phase": "plugin-dep-marketplace",
    "requirement": "R1",
    "status": "verified"
  },
  "record_type": "project:assessment",
  "recorded_at": "2026-10-11T06:52:17+00:00",
  "relationships": {},
  "revision": "sha256:4fdee1adeab97f393547ff4f65ffd3590be52636da8522d5a0c3fa5068a5d652",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "plugin-dep-marketplace-R1",
  "time": {
    "as_of": "2026-10-11T06:52:17+00:00"
  }
}
---

## Evidence

check-run rec-133596a3-9698-4c2b-aeaa-ae7ab76e82f5 pass on 40db2970236ac7ff04afd9eaf08292f072a912a2: claude plugin validate . and dependency/marketplace asserts (covers dependency declare and both plugins listed).

## Missing

none

## Reason

Manifests declare the adaptive-artifacts dependency and list both plugins in the se-workflow marketplace; validate passed.
