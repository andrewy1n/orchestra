## Close

Close is the last phase-end step. With a Landing section, it runs after
the human merges the phase branch. When `[land] adapter` is
`github-pr`, use the adapter's close instructions in this brief. Another
adapter ships its own close step; without one, close the phase by hand.

At phase close, the parent removes each task worktree `<repo>/.worktrees/{phase}--<task-slug>` for that phase.

At phase close, the parent deletes each `task/{phase}/<task-slug>` branch that is contained in the phase branch.

Without a Landing section, or without an adapter close step, close the
phase by hand when the gate holds.

Close the phase; close the phase position (`subject` = phase slug,
`status: closed`) only when a note position exists; update effort
position narrative (`subject` = focus). Keep `scope` identical to the predecessor's. Set `phase`
to the next phase the narrative names — pointer only; current phase is still derived from `score:phase`
state:

```bash
canon update --type score:phase --id <phase-id> \
  --transition done --expected-revision <revision>

canon supersede --type score:position --id <phase-position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type score:position --id <effort-position-id> \
  --expected-revision <revision> \
  --payload '{"position":"{phase} done; next up: <next-phase-slug>","scope":"<unchanged from predecessor>","effort":"{effort}","phase":"<next-phase-slug>"}'
```

Skip phase close commits for incidental. On revision
conflict, re-read effort position and retry. Plan the next phase only
after close. Do not materialize the next phase's tasks unless asked
(`tasks`).

If no `planned`/`in_progress` phase remains for this effort, ask
whether more phases follow. Yes → stop for `tasks`. No → close
the effort (`status: closed` on goal and position; `supersede` merges
payload so other fields carry over):

```bash
canon supersede --type score:effort --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type score:position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'
```

Reopen later: kinds-and-focus, Closing and reopening.

At `auto-phases`, plan and promote the next phase without asking. At
`gated` and `auto-plan`, ask first. At every level, stop for a failed check,
a needs-human finding, a push, or a merge.
