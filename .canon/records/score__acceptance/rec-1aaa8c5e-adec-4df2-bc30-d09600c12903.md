---
{
  "id": "rec-1aaa8c5e-adec-4df2-bc30-d09600c12903",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "A forged stored check-run does not change the verdict",
    "effort": "evidence-layer",
    "method": "tdd",
    "phase": "claims-manifest",
    "requirement": "R1",
    "verify_command": "python3 -m pytest tests/test_verdict.py -q -k forged_check_run"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-17T05:02:42+00:00",
  "relationships": {},
  "revision": "sha256:2a38f559121b8f1fe1dafff15d6ab199a1cba3c303d3e034ca72c10098ec2109",
  "subject": "verify-claims-manifest-forge",
  "time": {
    "as_of": "2026-10-17T05:02:42+00:00"
  }
}
---

