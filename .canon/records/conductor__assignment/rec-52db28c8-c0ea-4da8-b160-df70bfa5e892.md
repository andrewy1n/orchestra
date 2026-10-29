---
{
  "id": "rec-52db28c8-c0ea-4da8-b160-df70bfa5e892",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "verify-spec-analyze-agent",
    "work_item": "verify-spec-analyze"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-29T08:27:49+00:00",
  "relationships": {},
  "revision": "sha256:6d0a7857b248ef1e33f16e9b76f78d6f664ae59ac0be4102d5fa75b915044a77",
  "subject": "verify-spec-analyze"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/spec-analyze` (branch `phase/spec-analyze` for the closing verification, otherwise `task/spec-analyze/verify-spec-analyze`). Write only under it. Do not touch `.canon/`, other worktrees, or the primary checkout. Do not commit; the parent commits. The closing verification runs checks and returns evidence; it does not edit the tree.
Earlier waves are merged into the phase branch this worktree starts from. This task runs alone in its wave. The test files under `tests/` are frozen oracles; make them pass without editing them.

### Work-item (quote)

## Description

Prove the phase exit criteria hold together: run every analyze test file, run the integration check through the real CLI entry point, then check this phase's own records with `orchestra analyze`.

R1: `orchestra analyze <phase-slug>` exits 0 when no check reports an error.

R2: `orchestra analyze <phase-slug>` exits 1 when at least one check reports an error.

## Approach

Run the three test files, the integration test that calls the CLI as a subprocess against a temporary store, and `orchestra analyze spec-analyze` against the real store in plan stage. Report evidence only; do not edit the tree.

### Requirements (quote by id)

R1: `orchestra analyze <phase-slug>` exits 0 when no check reports an error.

R2: `orchestra analyze <phase-slug>` exits 1 when at least one check reports an error.

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
- analyze-stage-flag: Explicit --stage plan|close flag, default plan
