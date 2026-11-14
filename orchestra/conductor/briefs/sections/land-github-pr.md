# Land with the github-pr adapter

Use this guide when `[land] adapter` is `github-pr` in `orchestra.toml`.
The shared `phase-end.md` covers every landing adapter. This guide covers
what only the GitHub adapter has: a PR, CI checks on it, and
`orchestra close`.

## After land

Land pushes the phase branch and opens the PR. The PR title is the phase
title with its slug. The description says what the PR is for (the phase
Problem), gives the approach and the exit criteria, then carries the
proof packet under its own heading. Land waits for CI. A second land
reuses the PR and updates its title and description to match the phase
and the new proof packet. Each land run writes a `conductor:landing` record. When
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
6. Run `orchestra land --phase {phase}` again. Land pushes the
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
