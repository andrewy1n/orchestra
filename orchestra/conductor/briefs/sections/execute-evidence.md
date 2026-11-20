6. Mid-flight term changes (not status pings): message the subagent
   directly (it cannot read the store) and record the amendment,
   keyed to the work-item. Inline: record the same amendment and keep
   implementing:

```bash
canon create --type conductor:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","effort":"{effort}"}' \
  --body "## Correction

<the correction, as sent to the executor>"
```

7. When the task finishes, the per-task Landing commit (step 5) must
   already exist before `verify`. Record the evidence block
   verbatim — it is the record, not raw material to cherry-pick:

```bash
canon create --type conductor:execution-report \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","result":"<pass|fail|blocked|abandoned>","verdict":"<pass|fail|delta|inconclusive>","revision":"<git sha or dirty>"}' \
  --body "<the evidence block, verbatim>"
```

   Then run `verify` here. Its task verification instructions come from
   `orchestra workflow brief --skill verify`. verify for a task other than the
   work-item that depends_on every other phase work-item runs in that
   task worktree. It derives investigation / finding /
   check-run from this execution-report (not chat memory) and closes
   or leaves `in_progress`. `tdd`/`check` results come from
   `orchestra check` (verify runs it). Manual/review check-runs
   and the suite check-run (`orchestra suite record`, subject
   `{phase}-suite`) stay parent writes. Keep the `run_id` from
   `orchestra suite start`; pass it to poll, collect, record, or cancel.
   Use `--timeout <seconds>` to bound a run. Cancellation requires its
   explicit run ID.

   When the acceptance claim is in `.tuner/manifest.json`, run
   `orchestra verify verdict` before `done` (same command as step 4). Non-zero →
   leave `in_progress`.

   Do not supersede or re-derive readiness — dependents flip
   `derived.ready` when a dependency reaches terminal success; the
   next wave's `list` sees it.
8. At wave end, the parent merges each passing task branch of a task
   other than the work-item that depends_on every other phase
   work-item into `phase/{phase}`. Run those merges in the phase
   worktree `<repo>/.worktrees/{phase}`. Those wave-end merges
   run in task-slug order. The wave-end integration does not rebase
   the task branch. The parent does not merge a task branch whose
   check did not pass. `orchestra wave end` also holds tasks with open
   questions and their dependents.

```bash
orchestra wave end {phase}
```

   When a merge between a task branch and the phase branch conflicts,
   the parent leaves that conflict unresolved. When a merge between a
   task branch and the phase branch conflicts, the parent opens a
   blocking continuity question on the effort. Scope that question
   `merge:<task-slug>`. When a merge between a task branch and the
   phase branch conflicts, the parent does not start the next wave.
   Do not abort the merge. When both tasks can keep their behavior,
   edit the conflicted files in the phase worktree to keep both changes, stage them with `git add`
   and run `orchestra wave resolve {phase} <task-slug>`. When the
   two tasks need competing behavior, leave the question open and ask
   the user.

```bash
canon create --type score:continuity-question \
  --subject "{effort}" \
  --payload '{"owner":"user","blocking":true,"scope":"merge:<task-slug>"}'
```

   Start the next wave only after every passing, unblocked branch has
   merged cleanly. After the last implementation wave's
   execution-reports, return to step 3 for the closing verification
   task (do **not** write an integration-report before verification).

   With Landing, `orchestra wave start` runs the unique closing task
   after every other live phase task is done and integrated into the
   phase branch. It checks the phase source and active acceptances,
   writes the runner execution-report, and closes the task when all
   gates pass. A failed check leaves the task `in_progress`; run
   `wave start` again after fixing the cause. A manual acceptance
   waits for human sign-off. Without Landing, use the normal executor.
