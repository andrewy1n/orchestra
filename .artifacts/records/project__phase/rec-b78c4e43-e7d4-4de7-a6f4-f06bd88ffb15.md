---
{
  "base_kind": "phase",
  "id": "rec-b78c4e43-e7d4-4de7-a6f4-f06bd88ffb15",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "effort": "workflow-loop",
    "ordinal": 22,
    "title": "Oracle author, freeze, and amendments"
  },
  "record_type": "project:phase",
  "recorded_at": "2026-10-16T21:04:34+00:00",
  "relationships": {},
  "revision": "sha256:bc7f86651c9f26205a6ea8aae4849e2b73ca788319a1d16fb831601e80b43391",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "oracle-witnesses"
}
---

## Problem

The same agent writes the code, the tests, and chooses verify_command. Nothing checks that the oracle can tell a wrong implementation from a right one. Frozen hashes and a separate oracle author are the intended fix.

## Approach

Full oracle loop (decisions: `oracle-loop-shape`, `oracle-author-grain`, `oracle-amendment-type`, `assertion-level-red`, `amendment-approver`). Spec/design: `oracle-witnesses`.

1. Contract: freeze fields on acceptance (`test_ids`, `oracle_hashes`); new `project:oracle-amendment` (sections Reason/Change; status requested|approved|rejected).
2. Assertion-level red: classify pytest fail output; `aff check` records `failing_node_ids` on fail.
3. close-batch: for oracle-backed tdd (acceptance has freeze fields), refuse hash drift without approved amendment and refuse missing assertion-level red.
4. Skills: plan-phase one phase-scoped oracle author + freeze after red; execute-phase no edit frozen files + amendment path; verify-work mechanical verify.
5. Verify exit criteria through real close-batch CLI + skill/contract tests.

**Session shape:** more than one
**Executor:** subagent
**Human stops:** plan review; Landing merge into `main` (no push)
**Collision notes:** Wave 1 parallel — `oracle-contract` owns `contract/project-design.json`; `oracle-assertion-red` owns `affidavit/check.py` + new classifier module/tests. Wave 2 parallel — `oracle-freeze-close` owns `affidavit/close_batch.py` + `tests/test_close_batch.py` (oracle cases); `oracle-skills` owns `skills/plan-phase`, `skills/execute-phase`, `skills/verify-work` + skill/plan-trace consistency tests. Do not cross those ownership lines in a wave.

## Exit criteria

- Oracle-backed `tdd` acceptances carry frozen test ids/hashes; plan-phase documents the single oracle-author dispatch and assertion-level red gate.
- `project:oracle-amendment` exists; close refuses silent hash changes and non-assertion reds; tests cover refuse and happy path.
- execute-phase and verify-work skills match the loop; `tests/test_skill_contract_consistency.py` and the close/oracle tests this phase adds are green.
- A requirement can only close when its frozen oracle tests failed at base on an assertion and pass at head unchanged or with an approved amendment.

## Landing

- **branch:** `phase/oracle-witnesses`
- **worktree:** `/home/andrewyin/affidavit--oracle-witnesses`
- **base:** `main`
- **close:** commit code on the phase branch; merge that branch into `main`; commit the store on the primary checkout
- **push:** not a stop (do not push)
