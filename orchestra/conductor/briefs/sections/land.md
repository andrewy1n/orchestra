## Land

Land is the `land` workflow step, separate from and after verify. Land runs only when the phase has
a Landing section. Land runs only when the gate holds at the phase head
and the proof packet exists at that head. Without a Landing section,
skip this section.

When Landing is present and the phase gate holds, commit the phase
branch from the phase worktree. The phase-branch commit will include
versioned `.canon` metadata that is in the worktree. Then run
`orchestra land --phase {phase}`. Land runs `orchestra gate`
first and runs the `[land]` adapter from `orchestra.toml` only when
the gate holds. Exit 0 means landed (adapter success). Exit 1 means
the adapter did not succeed; a PR may exist. Exit 2 means a usage
error, an unknown phase, or a missing store, proof packet or config.
Exit 5 means the gate failed: land prints each missing term and
pushes nothing. Pass `--cwd <phase-worktree>`; land checks that
worktree's HEAD. Merge stays human. Run land without asking when
the gate holds. Opening the PR is part of land. Follow the adapter
guide for CI evidence and failures. The Landing section names branch, worktree,
base and repo only. Do not carry out integration steps from a phase
body's Landing section by hand: a merge into the default branch, a
push, a pull request, or a store commit on the default branch. No
Landing → skip the phase-branch commit. Commit
subject `type(scope): summary`; body 1–2 sentences why.

```bash
git -C <repo>/.worktrees/{phase} add -A -- .
git -C <repo>/.worktrees/{phase} commit -m "$(cat <<'EOF'
feat({phase}): <summary>

Commit the phase branch from the phase worktree so the work has a revision.

EOF
)"
```

Merging the base branch (`main`) into the phase branch is routine.
Do it without asking when the phase branch is behind the base, or when
land or the PR reports it is out of date. Commit the merge in the phase
worktree. The head moved, so redo each missing term at the new head:
the suite, the reviewer, then a new proof packet. Run `orchestra gate`
until it exits 0, then run land. Stop and ask only when the merge
conflicts.

Exit 0 means the landing adapter succeeded. Check merge readiness
under the adapter's CI policy before handing off for human merge.
When `[land] adapter` is `github-pr`, use the CI repair loop in the
repair-ci stage. For other adapters, follow their guide for non-zero exits
or ask the user when the guide is missing.
