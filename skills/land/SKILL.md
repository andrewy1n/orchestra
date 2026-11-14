---
name: land
description: >-
  Commit a verified phase branch, push it, and open or update its pull
  request. Use when the workflow routes to land.
---

# Land a phase

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md),
[kinds-and-focus.md](references/kinds-and-focus.md), and
[record-mechanics.md](references/record-mechanics.md). Follow the Land
section of [phase-end.md](references/phase-end.md). When `[land] adapter` is
`github-pr`, follow [land-github-pr.md](references/land-github-pr.md). Follow
[retry-loop.md](references/retry-loop.md) and
[execute-mechanics.md](references/execute-mechanics.md) for CI repairs.

## Own

- Commit the phase branch from the phase worktree.
- Run `orchestra land --phase <phase-slug>` without asking.
- Repair a failed CI check through the CI repair loop.
- Stop when `orchestra land` exits 0. The phase now awaits the human merge.

## Steps

1. Resolve the phase and its worktree. Run `orchestra gate <phase-slug>`.
   Stop if it fails. Verify owns the gate and the proof packet.
2. Merge the base branch into the phase branch when it is behind. Do not
   ask. Stop only on a merge conflict.
3. Commit the phase worktree. Run
   `orchestra land --phase <phase-slug> --cwd <phase-worktree>`.
4. On exit 1 with the `github-pr` adapter, run the CI repair loop. On any
   other non-zero exit, stop and ask.
5. Report the PR and the landing result.

## Do not

- Ask before you run land or open the pull request
- Merge into the default branch, or push it
- Run close before the human merge
- Hand-edit the landing record
