---
{
  "id": "rec-aaf4b93d-ba7a-41a6-b68f-fac64ef267e9",
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
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-19T03:23:37+00:00",
  "relationships": {},
  "revision": "sha256:9df0e7217f450324206e46dd4f6e90acf0066c4f57252a285e3cc52547f31c25",
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
