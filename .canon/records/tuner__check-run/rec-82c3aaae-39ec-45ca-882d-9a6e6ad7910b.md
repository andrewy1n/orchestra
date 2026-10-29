---
{
  "id": "rec-82c3aaae-39ec-45ca-882d-9a6e6ad7910b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-361d9cc1-b8b5-4ac7-9877-8f8ac70660db",
    "duration_s": 3.277272,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-361d9cc1-b8b5-4ac7-9877-8f8ac70660db",
      "rec-3f0bfee9-691a-4909-8b13-245eabdc6f6b"
    ],
    "method": "check",
    "output_sha256": "3a069e6b409cf657227c4c716e8305c1b4a0083dc6bee2eda6ed806c93626e88",
    "requirement": "R10",
    "result": "pass",
    "revision": "9ffd2768a9badf1dffebc49d1bf868acea25179a",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T19:01:36+00:00",
  "relationships": {},
  "revision": "sha256:a903412a786ce910a62a5f1267369724f41ad25d525669610eed8be7f8aa2ac6",
  "subject": "verify-node-ci-type-check"
}
---

> dashboard-ui@0.0.0 check
> svelte-check --tsconfig ./tsconfig.app.json && tsc -p tsconfig.node.json

1793300495474 START "/home/andrewyin/orchestra/.worktrees/node-ci/dashboard/web/ui"
1793300495476 COMPLETED 423 FILES 0 ERRORS 0 WARNINGS 0 FILES_WITH_PROBLEMS
