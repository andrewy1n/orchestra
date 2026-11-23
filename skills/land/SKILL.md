---
name: land
description: >-
  Commit a verified phase branch, push it, and open or update its pull
  request. Use when the workflow routes to land.
---

# Land a phase

Requires `canon` and `orchestra` on PATH. Run `orchestra workflow brief <phase> land` for your instructions, or use the `brief` that `orchestra workflow next` returns. If `orchestra` is not on PATH, stop and tell the user to install orchestra.

## Own

- Commit the phase branch from the phase worktree.
- Run `orchestra land --phase <phase-slug>` without asking.
- With `[merge_evidence]` configured, check the published PR with
  `orchestra merge-evidence --phase <phase-slug>`.
- Repair a failed CI check through the CI repair loop.
- Report the PR and its readiness for a human merge.

## Steps

1. Resolve the phase and its worktree. Run `orchestra gate <phase-slug>`.
   Stop if it fails. Verify owns the gate and the proof packet.
2. Merge the base branch into the phase branch when it is behind. Do not
   ask. Stop only on a merge conflict.
3. A merge moves the head. After a merge, redo the verification at the new
   head: run the suite and the reviewer, then write a new proof packet, as
   the verify skill describes. Run `orchestra gate` until it exits 0.
4. Commit the phase worktree. Run
   `orchestra land --phase <phase-slug> --cwd <phase-worktree>`.
5. Follow the generated brief for the adapter. For GitHub PRs, use
   `orchestra merge-evidence` after publication when configured. Otherwise
   `orchestra land` waits for CI. Repair confirmed failures through the CI
   repair loop. Refresh pending evidence when the checks finish. Stop and
   ask when the brief gives no recovery path for a reported failure.
6. Report the PR, landing result, and any remaining merge blockers.

## Do not

- Ask before you run land or open the pull request
- Merge into the default branch, or push it
- Run close before the human merge
- Hand-edit the landing record
