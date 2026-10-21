---
{
  "base_kind": "instruction",
  "id": "rec-f44daa93-4c51-4f4a-98a1-0ead59b8feb0",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "subagent-skills-stamp",
    "work_item": "skills-no-aff-runner"
  },
  "provenance": {
    "sources": [
      "skills-no-aff-runner"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-21T06:53:53+00:00",
  "relationships": {},
  "revision": "sha256:902a18486fff7b19d5c834d168d6f1b38089ffab59e6231e974ed8466c0db706",
  "subject": "skills-no-aff-runner",
  "time": {
    "observed": "2026-10-21T06:53:53+00:00",
    "recorded": "2026-10-21T06:53:53+00:00"
  }
}
---

## Orientation

Territory: Orchestra worktree `/home/andrewyin/orchestra/.worktrees/evidence-authority` only (skills/, shared/, tests/).
Do not edit frozen oracle test files from wave 1. You MAY create `tests/test_skill_runner_stamp.py` (not frozen).
Do not edit `.artifacts/` or call `adaptive-artifacts`.
Commit on phase branch when done.

### Work-item (quote)

## Description

R7: Orchestra skill and skill-reference text do not instruct creating a method `tdd` or `check` check-run with `runner` set to `aff`.

## Approach

Rewrite skill and reference docs (including `phase-end.md` and close-batch request examples) so `tdd`/`check` runner stamps say `orchestra`, and remove hand-typed `adaptive-artifacts create` examples that stamp `runner: "aff"`. Extend or add a skill scanner test that fails fixture text creating a `tdd`/`check` check-run with `runner: "aff"` and passes current skills after the rewrite.

### Requirements (quote by id)

R7: Orchestra skill and skill-reference text do not instruct creating a method `tdd` or `check` check-run with `runner` set to `aff`.

### Design / decisions (quote)

evidence-authority-approach: honest-stamp-aff-claim-gate
runner-marker: orchestra
legacy-runner-stamp: refuse-aff
