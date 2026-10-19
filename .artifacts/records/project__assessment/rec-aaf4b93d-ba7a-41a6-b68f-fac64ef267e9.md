---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-aaf4b93d-ba7a-41a6-b68f-fac64ef267e9",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "packaging",
    "missing": "",
    "next": "release",
    "phase": "installer-wizard",
    "requirement": "R5",
    "status": "verified"
  },
  "record_type": "project:assessment",
  "recorded_at": "2026-10-19T03:23:37+00:00",
  "relationships": {},
  "revision": "sha256:328ee62b49379702210ff6d762c0ffb4cb53716b8816debbcda252a23a65be17",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "installer-wizard-R5",
  "time": {
    "as_of": "2026-10-19T03:23:37+00:00"
  }
}
---

## Evidence

Check-run rec-1f9fbc46-d1e2-49f3-b66c-dd1f035d6b43 passed at revision f70d46ffba8b383757dc9c12de6e43c833a7346a. It ran `python3 -m pytest tests/test_installer_wizard.py -q -k empty_selection_refuses`.

## Missing

none

## Reason

A blank answer with no detected hosts raises the refusal instead of proceeding.
