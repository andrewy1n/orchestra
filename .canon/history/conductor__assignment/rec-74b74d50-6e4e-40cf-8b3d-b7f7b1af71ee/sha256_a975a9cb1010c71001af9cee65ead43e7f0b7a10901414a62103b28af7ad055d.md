---
{
  "id": "rec-74b74d50-6e4e-40cf-8b3d-b7f7b1af71ee",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "inline",
    "work_item": "fix-order-line-test"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-29T08:41:38+00:00",
  "relationships": {},
  "revision": "sha256:a975a9cb1010c71001af9cee65ead43e7f0b7a10901414a62103b28af7ad055d",
  "subject": "fix-order-line-test"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/spec-analyze--fix-order-line-test` (branch `phase/spec-analyze` for the closing verification, otherwise `task/spec-analyze/fix-order-line-test`). Write only under it. Do not touch `.canon/`, other worktrees, or the primary checkout. Do not commit; the parent commits. The closing verification runs checks and returns evidence; it does not edit the tree.
Earlier waves are merged into the phase branch this worktree starts from. This task runs alone in its wave. The test files under `tests/` are frozen oracles; make them pass without editing them.

### Work-item (quote)

## Description

R21: The execute-phase skill tells the agent to run `orchestra analyze <phase-slug> --stage close` after the closing verification and before the reviewer, and to refuse to start the reviewer while it exits 1.

## Approach

The execute-phase skill's phase-end order line now reads `closing verification → analyze → reviewer → integration-report → suite → phase gate`. Update the expected string in `tests/test_tiered_verification.py::test_execute_phase_documents_suite_policy_after_reviewer_and_check_run` to match. Change nothing else; do not edit `tests/test_analyze*.py`.

### Requirements (quote by id)

R21: The execute-phase skill tells the agent to run `orchestra analyze <phase-slug> --stage close` after the closing verification and before the reviewer, and to refuse to start the reviewer while it exits 1.

### Design / decisions (quote)

#### Invariants

- No write to the store or the disk.
- Exit 1 if and only if an error finding exists.
- Same store and arguments give the same output.
- `orchestra/score/` imports only `canon`.

#### Assumptions

- Requirement lines are `Rn: <text>` and one per line.
- `criterion_id` is the acceptance record id.
- One active specification and one active design per phase.

#### Decisions
- analyze-gate-strength: Skill gates at plan review and phase close; engine gates deferred
