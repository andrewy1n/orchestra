---
{
  "id": "rec-be84a29b-7214-4ca2-a94d-2d51ec2dc6ab",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "a pytest runs bin/orchestra check --help and bin/orchestra close-batch --help and each exits 0",
    "effort": "evidence-layer",
    "method": "check",
    "phase": "standalone-aff",
    "requirement": "R3",
    "verify_command": "cd \"$HOME/orchestra\" && python3 -m pytest tests/test_affidavit_check.py -q -k orchestra_subcommand_help"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-17T23:07:38+00:00",
  "relationships": {},
  "revision": "sha256:9f1456e2ce46cc268e1e3065542109c9927268ba2bbd7af616eb6a0093c0c9e2",
  "subject": "fix-orchestra-help-tests",
  "time": {
    "as_of": "2026-10-17T23:07:38+00:00"
  }
}
---

