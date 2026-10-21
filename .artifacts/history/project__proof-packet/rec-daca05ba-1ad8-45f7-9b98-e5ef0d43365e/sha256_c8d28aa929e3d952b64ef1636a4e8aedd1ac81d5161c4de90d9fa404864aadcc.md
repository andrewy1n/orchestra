---
{
  "base_kind": "observation",
  "id": "rec-daca05ba-1ad8-45f7-9b98-e5ef0d43365e",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "c880f5f1668765a945acc56a596d83ff67f59328",
    "effort": "workflow-loop",
    "kind": "commands",
    "phase": "task-worktrees",
    "revision": "ac64d0816c9e14410dce73596abbe3681637d0cc"
  },
  "provenance": {
    "sources": [
      "task-worktrees"
    ]
  },
  "record_type": "project:proof-packet",
  "recorded_at": "2026-10-21T05:40:28+00:00",
  "relationships": {},
  "revision": "sha256:c8d28aa929e3d952b64ef1636a4e8aedd1ac81d5161c4de90d9fa404864aadcc",
  "subject": "task-worktrees",
  "time": {
    "observed": "2026-10-21T05:40:28+00:00",
    "recorded": "2026-10-21T05:40:28+00:00"
  }
}
---

## Look

`skills/execute-phase/SKILL.md` now gives each non-verification task its own branch `task/<phase-slug>/<task-slug>` and worktree `<repo>/.worktrees/<phase-slug>--<task-slug>`. The task commits and is verified there. Passing branches merge into the phase branch at wave end. `skills/execute-phase/references/phase-end.md` removes those worktrees and deletes merged task branches at phase close.

## Machine

- phase: task-worktrees
- effort: workflow-loop
- base: c880f5f1668765a945acc56a596d83ff67f59328
- revision: ac64d0816c9e14410dce73596abbe3681637d0cc
- proof kind: commands
- command: `python3 -m pytest tests/test_task_commit.py tests/test_execute_landing.py tests/test_task_worktrees.py -q` (37 passed at phase head)

## Attention

Phase-end cleanup is stated as sentences in `phase-end.md`. This phase did not create `task/task-worktrees/*` branches, so close has no task worktree to remove and no task branch to delete.

## Diff

```
 skills/execute-phase/SKILL.md                | 153 ++++++++++++++++++++-----
 skills/execute-phase/references/phase-end.md |   4 +
 tests/test_task_commit.py                    |  30 +++---
 tests/test_task_worktrees.py                 | 217 +++++++++++++++++++++++++++++++++
 4 files changed, 370 insertions(+), 34 deletions(-)
```
