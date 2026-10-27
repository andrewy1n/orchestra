---
{
  "id": "rec-e1a4d73d-fc84-4ee9-97dd-c5ddc7a3f3ca",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "evidence-layer",
    "missing": "",
    "next": "release",
    "phase": "audit-differential",
    "requirement": "R2",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-18T04:23:00+00:00",
  "relationships": {},
  "revision": "sha256:378ec82c95810edc72d6fbf5bb432692a85b631c0b2e93df712d511cbacbbb30",
  "subject": "audit-differential-R2",
  "time": {
    "as_of": "2026-10-18T04:23:00+00:00"
  }
}
---

## Evidence

red rec-0bfaef1d-fd57-4ca7-bce2-971fa39f286b at a12a5f1 then green rec-3a946cfc-304a-4537-b3e8-082c0747582b at 846120f; oracle tests/test_audit_probes.py frozen.

## Missing

none

## Reason

Requirement R2 passes after assertion-level red on the failing oracle tip.
