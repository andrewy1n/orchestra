---
{
  "id": "rec-9175aacc-f872-4bc9-94be-6abdd784bec1",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "composer",
    "executor": "cursor",
    "work_item": "fix-engage-idea-review"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-28T07:44:31+00:00",
  "relationships": {},
  "revision": "sha256:6b483c74c4a059050af3559c8546bfa8755dc5d0f1d08928101f2ba2abbc4ed3",
  "subject": "fix-engage-idea-review"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/engage-from-idea--fix-engage-idea-review` (branch task/engage-from-idea/fix-engage-idea-review). Cursor worker.

### Work-item (quote)

## Description

R5: `engage` takes the idea's effort as the focus when the idea has an effort.
R7: The routing line carries `idea: <subject> | none`.

## Approach

In skills/engage/SKILL.md: step 3 starts with an entry condition that skips it when the ask names an idea; step 4 sets `idea: <idea-subject>` on the routing line, reopens a closed effort as step 3 does, and overrides the skip-settle-phase and incidental shortcuts of step 5 so the idea path always routes through settle-phase (phase: new) or init. In init and settle-phase, skip the promotion and say so unless the idea status is `open`. Add test assertions for each.
