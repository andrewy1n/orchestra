---
{
  "id": "rec-c6f57f2f-cef8-4daf-b8f1-7899cd1a7e27",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "tests/test_evidence_loop.py drives adaptive-artifacts on a fresh store through release ready, a check-run with no level or next, a repeated implementation failure that routes to design, a design route, integration failure, insufficient evidence, and a legacy pass check-run.",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "evidence-loop",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_evidence_loop.py -q"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-05T02:04:03+00:00",
  "relationships": {},
  "revision": "sha256:7b9b50f88574fa734193e955c93a757ea1dbf6ac96fde904d295e74966b3358f",
  "subject": "verify-evidence-loop",
  "time": {
    "as_of": "2026-10-05T01:56:38+00:00"
  }
}
---

