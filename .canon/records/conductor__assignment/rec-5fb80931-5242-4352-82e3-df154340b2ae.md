---
{
  "id": "rec-5fb80931-5242-4352-82e3-df154340b2ae",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "analyze-close-checks-agent",
    "work_item": "analyze-close-checks"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-29T08:22:30+00:00",
  "relationships": {},
  "revision": "sha256:1ace4b86de421ddca6484e20bd5e3c051d65b5da0ded5b1dc24bec5881edb3cd",
  "subject": "analyze-close-checks"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/spec-analyze--analyze-close-checks` (branch `task/spec-analyze/analyze-close-checks`). Write only under it. Do not touch `.canon/`, other worktrees, or the primary checkout. Do not commit; the parent commits.
Earlier waves are merged into the phase branch this worktree starts from. This task runs alone in its wave. The test files under `tests/` are frozen oracles; make them pass without editing them.

### Work-item (quote)

## Description

R17: In the `close` stage, an active acceptance of the phase with no `tuner:check-run` is an error with code `acceptance-no-check-run`.

R18: In the `close` stage, an active acceptance whose latest `tuner:check-run` result is not `pass` is an error with code `acceptance-not-passing`.

## Approach

Extend `analyze_phase` so `stage="close"` also emits check-run findings. For each active acceptance of the phase, collect `tuner:check-run` records whose `criterion_id` equals the acceptance record id. Take the latest by `recorded_at`. Emit `acceptance-no-check-run` when none exist and `acceptance-not-passing` when its result is not `pass`. Put the acceptance id in the message. The `plan` stage emits neither.

### Requirements (quote by id)

R17: In the `close` stage, an active acceptance of the phase with no `tuner:check-run` is an error with code `acceptance-no-check-run`.

R18: In the `close` stage, an active acceptance whose latest `tuner:check-run` result is not `pass` is an error with code `acceptance-not-passing`.

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
- analyze-stage-flag: Explicit --stage plan|close flag, default plan

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen:
- `tests/test_analyze.py`
Do not edit them. An oracle hash or test-id change is a signed amendment in `.tuner/manifest.json`. orchestra verify verdict accepts or rejects it. A non-zero exit means the acceptance is not done.
