---
{
  "id": "rec-aea1dfbb-7171-40ff-a6e9-ee1dc706acae",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "library-boundary",
    "missing": "",
    "next": "release",
    "phase": "affidavit-library",
    "requirement": "R1",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-21T10:23:06+00:00",
  "relationships": {},
  "revision": "sha256:efeabdbd5d0a2bc24fd4f63564b37bea6a7b88bb38ca57352f1f33c21732f9aa",
  "subject": "affidavit-library-R1",
  "time": {
    "as_of": "2026-10-21T10:23:06+00:00"
  }
}
---

## Evidence

Red check-run rec-fe883ac9-dcd6-496f-8813-fb160628bc9a is assertion-level fail at revision dirty with diff_sha256 e9e01e8537198af5905f71af47d8fb7a387135605d0dfd09f09161204cdae718. Green check-run rec-3eca21a1-0962-40ba-bf98-35b381276c72 passed at 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538. Frozen oracle hashes match: tests/test_store_client.py:sha256:39790bc3eec3954dfd957db28be1875d382ee304e08ba04dceb3dcd884c2da43.

## Missing

none

## Reason

R1 holds: observation creates an evidence-observation by calling Project.create, and the frozen test was not edited.
