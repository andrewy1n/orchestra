3. Group unblocked results by `derived.wave`. Lower ready waves come first.
   Re-run the step-2 list before each wave.

   When Landing is present, at the start of a wave, execute
   creates branch `task/{phase}/<task-slug>` from the current
   `phase/{phase}` tip for every task in that wave except the
   work-item that depends_on every other phase work-item. When Landing
   is present, at the start of a wave, execute adds worktree
   `<repo>/.worktrees/{phase}--<task-slug>` checked out on that
   task branch for every task in that wave except the work-item that
   depends_on every other phase work-item. execute does not
   create a task branch for the work-item that depends_on every other
   phase work-item. execute does not add a task worktree for the
   work-item that depends_on every other phase work-item. The
   work-item that depends_on every other phase work-item is dispatched
   in `<repo>/.worktrees/{phase}` on `phase/{phase}`.

   Re-dispatch of a task other than the work-item that depends_on
   every other phase work-item reuses branch
   `task/{phase}/<task-slug>`. Re-dispatch of a task other than
   the work-item that depends_on every other phase work-item reuses
   worktree `<repo>/.worktrees/{phase}--<task-slug>`. Before a
   re-dispatch continues, the parent merges `phase/{phase}` into
   the task branch when the task branch does not already contain the
   phase tip. If that merge conflicts, leave it unresolved, open a
   blocking continuity question on the effort, and do not start the
   next wave (same conflict rules as wave end).

   Create the branch and worktree only when they are missing, and only
   for a task other than the work-item that depends_on every other
   phase work-item. On re-dispatch, reuse them. Run the merge only
   when the task branch does not already contain the phase tip:

```bash
git branch task/{phase}/<task-slug> phase/{phase}
git worktree add <repo>/.worktrees/{phase}--<task-slug> task/{phase}/<task-slug>
git -C <repo>/.worktrees/{phase}--<task-slug> merge-base --is-ancestor phase/{phase} HEAD \
  || git -C <repo>/.worktrees/{phase}--<task-slug> merge phase/{phase}
```

   Read `payload.executor` on each ready task (`inline` | `subagent`;
   missing/empty → `subagent`). If the wave disagrees, or any value is
   other than those two, stop and name the tasks — do not spawn or
   transition. Follow `## Approach` in the brief; do not ask the user
   for an implementation recipe when it is present.
