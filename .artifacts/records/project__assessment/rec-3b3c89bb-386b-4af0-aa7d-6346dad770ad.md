---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-3b3c89bb-386b-4af0-aa7d-6346dad770ad",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "library-boundary",
    "missing": "",
    "next": "release",
    "phase": "aa-library",
    "requirement": "R7",
    "status": "verified"
  },
  "record_type": "project:assessment",
  "recorded_at": "2026-10-21T09:09:45+00:00",
  "relationships": {},
  "revision": "sha256:cf051afa778123e9ea99ca9fc13c3aae922b796a25ffc55d912b81b1ec929aee",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "aa-library-R7",
  "time": {
    "as_of": "2026-10-21T09:09:45+00:00"
  }
}
---

## Evidence

Red check-run rec-9f230c22-5bf4-402f-8074-7464982b4508 is assertion-level fail at revision dirty with diff_sha256 c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3. Green check-run rec-4042347a-79ed-4952-b258-8ab0edba30e9 passed at c979dd13c06c36eb1a4f9f042e97ec4846903d7a, which is the open-store commit. Frozen oracle tests/test_open_store.py matches sha256:d601c17196a93a7bcfc4ee5f461e5ab749d071b3575b111b1536d8144a596afd.

## Missing

none

## Reason

R7 holds: the frozen test passed on the open-store commit and the oracle file was not edited.
