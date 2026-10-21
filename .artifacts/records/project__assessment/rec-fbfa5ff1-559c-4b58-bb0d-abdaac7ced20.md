---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-fbfa5ff1-559c-4b58-bb0d-abdaac7ced20",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "library-boundary",
    "missing": "",
    "next": "release",
    "phase": "aa-library",
    "requirement": "R12",
    "status": "verified"
  },
  "record_type": "project:assessment",
  "recorded_at": "2026-10-21T09:09:40+00:00",
  "relationships": {},
  "revision": "sha256:66d23b45ac65db52d5608fa6c448a51d12d540ec0c43f64f92f1128113cccab5",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "aa-library-R12",
  "time": {
    "as_of": "2026-10-21T09:09:40+00:00"
  }
}
---

## Evidence

Red check-run rec-23ecc762-4078-4996-a4ef-60cc43e2b7c9 is assertion-level fail at revision dirty with diff_sha256 c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3. Green check-run rec-b40c006d-cf35-43d3-8f12-e22f463d9acb passed at c979dd13c06c36eb1a4f9f042e97ec4846903d7a, which is the open-store commit. Frozen oracle tests/test_open_store.py matches sha256:d601c17196a93a7bcfc4ee5f461e5ab749d071b3575b111b1536d8144a596afd.

## Missing

none

## Reason

R12 holds: the frozen test passed on the open-store commit and the oracle file was not edited.
