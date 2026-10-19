---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-42e9d09d-8bf3-4c5c-8abf-ba99dc9533c2",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "aff check and close-batch work with code in a phase worktree and store on primary checkout (--cwd); store discovery does not follow worktree cwd; revision comes from worktree HEAD",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "claim-witnesses",
    "requirement": "R5",
    "verify_command": "python3 -m pytest tests/test_affidavit_check.py tests/test_close_batch.py -k 'worktree or cwd_primary or store_cwd' -q"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-16T09:29:08+00:00",
  "relationships": {},
  "revision": "sha256:d00e58f0449d0ff155fc009a882a6f79b3a4e79d4e5616cd30ac1a9fa9b54359",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verify-path-test-gaps",
  "time": {
    "as_of": "2026-10-16T09:29:08+00:00"
  }
}
---

