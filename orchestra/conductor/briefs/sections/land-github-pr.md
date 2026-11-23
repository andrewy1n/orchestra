# Land with the github-pr adapter

Use this guide when `[land] adapter` is `github-pr` in `orchestra.toml`.
The phase-end step covers every landing adapter. This section covers
what only the GitHub adapter has: a PR, CI checks on it, and
`orchestra close`.

## After land

Land pushes the phase branch and opens the PR. The PR title is the phase
title with its slug. The description says what the PR is for (the phase
Problem), gives the approach and the exit criteria, then carries the
proof packet under its own heading. A second land
reuses the PR and updates its title and description to match the phase
and the new proof packet. Each completed adapter run writes a
`conductor:landing` record.

With `[merge_evidence]` configured, exit 0 from `orchestra land` means
publication succeeded. Run `orchestra merge-evidence --phase {phase}`
to record a recommendation for the PR head. Exit 0 means the evidence is
ready for human merge approval. On exit 1, read the check results and
phase blockers.

- Send confirmed required check failures on the PR head through the repair loop.
- If the remaining blockers are required checks still running on that head,
  refresh the evidence after those checks finish.
- If the evidence has any other blocker, stop and ask. Report the blocker,
  for example missing required-check configuration or results from GitHub's
  test merge commit.

On exit 2, stop and ask with the reported command error.

Without `[merge_evidence]`, `orchestra land` waits for CI. Exit 0
means CI passed. Merge stays human in both modes.

### CI repair loop

Repair a failed required check from `orchestra merge-evidence` or, when
the landing adapter waits for CI, when `orchestra land` exits 1 with a failed check.

1. Identify the failed checks in the evidence or land output. Read their logs with
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
   commit to the open PR. With `[merge_evidence]` configured, run
   `orchestra merge-evidence --phase {phase}` again for the new head.
   Otherwise the landing adapter reads CI again.
7. Repeat for any confirmed failures within the retry budgets.

Repairs follow the retry budgets in this brief:
`retry_max_redispatches` per task and `retry_max_fix_tasks` per phase.
When a retry budget runs out, open a `score:continuity-question` with
scope `retry:<repair-task-slug>` and a `tuner:finding`, as the retry rules
describe. Do not create another repair. Stop until the
user answers.

Hand off the PR for human merge when CI and phase evidence are ready.
