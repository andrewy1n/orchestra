## Steps

1. Run `orchestra handoff` if the handoff was not injected. Resolve
   **focus**. Read `orchestra view plan --effort {effort}` and blocking
   `continuity-question`s for that subject. Do not dispatch while a
   blocking question is open on this focus. A question with `scope`
   `plan-review:{phase}` gates only that phase; clear on approve:

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   Do not dispatch another effort's tasks.

   Before planned ready work, re-dispatch retryable `in_progress`
   items (same executor mode) using the retry rules in this brief. Then continue with the
   planned ready list.
2. Select dispatchable work-items (plan view omits `derived.ready`/`wave`):

```bash
canon list --type score:work-item --state planned \
  --where payload.effort={effort} --where payload.phase={phase} \
  --where derived.ready=true
```

   For `incidental`, drop `payload.phase` (it is `""`) and expect at
   most one result. `current-phase-slug` is the `score:phase` for
   this effort with `lifecycle_state` `in_progress` — never
   `score:position` `scope`. If none exist, stop and point to
   `tasks`. If several phases are `in_progress`, use the one
   named in context; ask if none is named.

   After plan review is answered and before the first wave, read
   `## Landing` from the phase body:

```bash
canon get --type score:phase --id <phase-id>
```

   When `## Landing` is present, ensure branch `phase/{phase}`
   from `main` and worktree `<repo>/.worktrees/{phase}`:

```bash
git branch phase/{phase} main
mkdir -p <repo>/.worktrees
git worktree add <repo>/.worktrees/{phase} phase/{phase}
```

   When Landing is present, code writes only under the worktree and
   store writes on the primary checkout (on `main`). `.canon`
   stays on that primary checkout. Task commits exclude `.canon`.
   When Landing is absent, a missing Landing section
   stays in the current checkout (incidental too); do not create a
   branch or worktree. When Landing is absent, execute does not
   create a `task/{phase}/<task-slug>` branch. When Landing is
   absent, execute does not add a
   `<repo>/.worktrees/{phase}--<task-slug>` worktree.
