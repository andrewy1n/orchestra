---
{
  "id": "rec-b58baac5-2bbb-4fa6-a490-7cc55b97f3c6",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "library-boundary",
    "missing": "",
    "next": "release",
    "phase": "aa-library",
    "requirement": "R10",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-21T09:09:44+00:00",
  "relationships": {},
  "revision": "sha256:3d42fed1297b8fe0c5130e98ace0ea13d7a24c51116ed39d5fc69605755b2566",
  "subject": "aa-library-R10",
  "time": {
    "as_of": "2026-10-21T09:09:44+00:00"
  }
}
---

## Evidence

Red check-run rec-00a9fe73-6861-423f-9fdf-8ff6472c57be is assertion-level fail at revision dirty with diff_sha256 c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3. Green check-run rec-941b7bf7-0a61-47ca-b810-1a68919f39b2 passed at c979dd13c06c36eb1a4f9f042e97ec4846903d7a, which is the open-store commit. Frozen oracle tests/test_open_store.py matches sha256:d601c17196a93a7bcfc4ee5f461e5ab749d071b3575b111b1536d8144a596afd.

## Missing

none

## Reason

R10 holds: the frozen test passed on the open-store commit and the oracle file was not edited.
