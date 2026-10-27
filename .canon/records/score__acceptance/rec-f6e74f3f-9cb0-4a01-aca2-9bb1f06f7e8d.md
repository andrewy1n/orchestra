---
{
  "id": "rec-f6e74f3f-9cb0-4a01-aca2-9bb1f06f7e8d",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "The close path imports affidavit.oracle_red, and no orchestra module imports affidavit.aa, affidavit.aa_resolve, affidavit.check, affidavit.policy, or affidavit.verdict",
    "effort": "evidence-layer",
    "method": "check",
    "phase": "standalone-aff",
    "requirement": "R4",
    "verify_command": "cd \"$HOME/orchestra\" && python3 -m pytest tests/test_affidavit_import_boundary.py -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-17T22:39:38+00:00",
  "relationships": {},
  "revision": "sha256:6bcc55c4a94754247b4ba152231cd5083a7457778c12c53c161b2dfa01706f65",
  "subject": "verify-standalone-aff-imports",
  "time": {
    "as_of": "2026-10-17T22:39:38+00:00"
  }
}
---

