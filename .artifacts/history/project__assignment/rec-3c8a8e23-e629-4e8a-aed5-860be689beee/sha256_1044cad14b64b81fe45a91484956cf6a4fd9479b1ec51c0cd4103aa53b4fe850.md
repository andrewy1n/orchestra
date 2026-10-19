---
{
  "base_kind": "instruction",
  "id": "rec-3c8a8e23-e629-4e8a-aed5-860be689beee",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "subagent-oracle-freeze-close",
    "work_item": "oracle-freeze-close"
  },
  "provenance": {
    "sources": [
      "oracle-freeze-close"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-16T20:34:31+00:00",
  "relationships": {},
  "revision": "sha256:1044cad14b64b81fe45a91484956cf6a4fd9479b1ec51c0cd4103aa53b4fe850",
  "subject": "oracle-freeze-close",
  "time": {
    "observed": "2026-10-16T20:34:31+00:00",
    "recorded": "2026-10-16T20:34:31+00:00"
  }
}
---

## Orientation

Territory: wave-2 parallel with oracle-skills. You own ONLY: affidavit/close_batch.py and oracle cases in tests/test_close_batch.py (helpers colocated with close if needed). Import classifier from affidavit/oracle_red.py (already landed). Do NOT edit skills/ or contract/.

Worktree: /home/andrewyin/affidavit--oracle-witnesses. Do not write .artifacts/. Do not call adaptive-artifacts.

Concurrency: sibling may commit in the same worktree. Before git commit:
  flock /tmp/oracle-witnesses-git.lock -c 'git -C /home/andrewyin/affidavit--oracle-witnesses add -A -- . ":!.artifacts" && git -C /home/andrewyin/affidavit--oracle-witnesses commit -m "oracle-freeze-close"'

Contract already has test_ids, oracle_hashes, and project:oracle-amendment. Classifier already exists.

## Requirements (R3, R5)

R3: Each oracle-backed acceptance stores frozen oracle test node ids and content hashes... The contract gains the payload fields needed for ids and hashes.

R5: The close path (close-batch / store-backed close) refuses tdd done when (a) the tree at the green revision's oracle files do not match the frozen hashes and no approved oracle-amendment covers the new hashes, or (b) there is no qualifying assertion-level red for that acceptance's frozen tests at base.

## Design Invariants

- Oracle author ≠ executor for oracle-backed tdd.
- Frozen hashes are the close authority for oracle file contents; agent prose is not.
- Assertion-level red is required before freeze and before done close.
- Parent session alone writes freeze fields, amendments, and assessments.

## Design Assumptions

- Pytest emits assertion failures in captured output in a form a small classifier can detect.
- One phase-scoped oracle author can cover multiple requirements without the executor feeding it implementation hints.
- Existing red-first ancestry rules remain; this phase adds freeze/assertion constraints on which reds qualify.

## Decisions

- oracle-loop-shape: full oracle loop
- assertion-level-red: red must be fail with assertion-level failing node
- amendment-approver: parent session approves
- oracle-amendment-type: new project:oracle-amendment type
