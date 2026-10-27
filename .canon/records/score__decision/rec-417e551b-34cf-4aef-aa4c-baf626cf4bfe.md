---
{
  "id": "rec-417e551b-34cf-4aef-aa4c-baf626cf4bfe",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "after evidence-kind, phase-end-evidence, and evidence-e2e",
    "choice": "standalone-aff runs before evidence-kind",
    "effort": "evidence-layer",
    "phase": "standalone-aff"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-17T09:25:40+00:00",
  "relationships": {},
  "revision": "sha256:d098716af1598c6d0e31ff8c98a23a8303f1ce5c781d7e50fffc20f20673482c",
  "subject": "standalone-aff-next",
  "time": {
    "as_of": "2026-10-17T09:25:40+00:00"
  }
}
---

## Rationale

aff still names workflow record types and the se-workflow store switch. Later evidence-layer phases assume the evidence boundary is already the product. standalone-aff runs next, before evidence-kind, so those phases are not built on the coupling this phase removes.

## Counter-argument

evidence-kind, phase-end-evidence, and evidence-e2e are already named and ordered. Inserting a phase in front delays them, and a narrower evidence_kind rule could land without waiting for the store client to leave this repo.
