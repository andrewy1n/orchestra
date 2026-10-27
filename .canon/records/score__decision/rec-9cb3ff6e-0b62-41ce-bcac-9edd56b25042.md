---
{
  "id": "rec-9cb3ff6e-0b62-41ce-bcac-9edd56b25042",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "leave the project field as affidavit",
    "choice": "bundled contract project becomes orchestra; ensure-store rewrites affidavit to orchestra",
    "effort": "evidence-layer",
    "phase": "orchestration-split"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-17T07:25:46+00:00",
  "relationships": {},
  "revision": "sha256:b92f8f64805149ed5fe51b744e5e4f533df2aea602b367702bb1a8823ed2d313",
  "subject": "contract-project",
  "time": {
    "as_of": "2026-10-17T07:25:46+00:00"
  }
}
---

## Rationale

The bundled contract's `"project"` becomes `orchestra`, matching the plugin. ensure-store today treats any other value as a foreign contract and stops. A work repo whose design still says `affidavit` is the previous id of this same contract, so ensure-store rewrites that field to `orchestra` and continues. Any other project value still stops the overlay.

## Counter-argument

Leaving `"project"` as `affidavit` would avoid rewriting every adopted store. The field is an identity check, not the plugin's display name, and those stores already say `affidavit`. A plugin named orchestra can ship that existing id and skip the migration.
