# Land with the github-pr adapter

Use this guide when `[land] adapter` is `github-pr` in `orchestra.toml`.
The shared `phase-end.md` covers every landing adapter. This guide covers
what only the GitHub adapter has: a PR, CI checks on it, and
`orchestra close`.

## After land

Land pushes the phase branch, opens the PR with the proof packet, and
waits for CI. Each land run writes a `conductor:landing` record. When
`orchestra land` exits 0, CI passed and the phase is awaiting merge.
`orchestra handoff` shows "Awaiting merge: PR n". Merge stays human.

### CI repair loop

Land waits for CI. When `orchestra land` exits 1 with a failed check,
repair it without a user step:

1. Read the failed checks in the land output. Read their logs with
   `gh run view <run-id> --log-failed`.
2. Create a repair work-item on the phase for the failing checks. Its
   acceptance is that each failing check passes. Count it against
   `retry_max_fix_tasks`.
3. Run the repair through the execute wave in the phase worktree. The
   repair uses the executor rules of a task.
4. After the repair passes its acceptance, commit the repair in the
   phase worktree.
5. The head moved. Run `orchestra gate`. Redo each missing term at the
   new head: the reviewer, then a new proof packet.
6. Run `orchestra land --phase <phase-slug>` again. Land pushes the
   commit to the open PR and reads CI again.
7. Repeat from step 1 until land exits 0.

Repairs follow the retry budgets in `retry-loop.md`:
`retry_max_redispatches` per task and `retry_max_fix_tasks` per phase.
When a retry budget runs out, open a `score:continuity-question` with
scope `retry:<repair-task-slug>` and a `tuner:finding`, as
`retry-loop.md` describes. Do not create another repair. Stop until the
user answers.

Land ends when `orchestra land` exits 0. The phase is then awaiting
merge. Merge stays human.

## Close

Close is the last phase-end step. It runs after the human merges the PR.
Run `orchestra close --phase <phase-slug>` from the main checkout, not
from a worktree that close removes. Close reads the landing record and
asks `gh` for the PR state. It acts only when the PR is merged. Exit 0
means close finished, found nothing left to do, or found the PR still
open. Exit 1 means close refused and named the path or branch: fix it,
then run close again. Exit 2 means a usage, store or `gh` error.

Close removes each task worktree `<repo>/.worktrees/<phase-slug>--<task-slug>`
and then the phase worktree. It deletes each `task/<phase-slug>/<task-slug>`
branch that is contained in the phase branch and then the
`phase/<phase-slug>` branch. It also updates the effort position, closes
the phase position, and marks the phase done. It skips each step already
done. Plan the next phase only after close.

Session start runs `orchestra close --all`, so a merge between sessions
closes on its own. A session that starts inside a worktree that close
would remove gets a refusal instead.

`orchestra close` needs the `github-pr` adapter and an authenticated
`gh`. Another adapter needs its own close step.
