# execute mechanics

Full step-by-step mechanics. SKILL.md keeps the judgment; this file is the manual fallback and the record of every contract.

## Execute the focused effort

Requires `canon` and `orchestra` on PATH and a live
orchestra store. If missing,
follow [ensure-store.md](references/ensure-store.md) then `init` (if no goal
for the focus) and `tasks`. Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Follow `verify`
after each task finishes (subagent return or inline).

**Single-writer:** only this parent may write via `canon`.
Subagents never write — including under any future `--read-only`
executor mode (that mode names what may be *read*; a subagent write
would race `--expected-revision`).

Task lifecycle is `planned -> in_progress -> done` (or `withdrawn`).
Orchestra moves a work-item to `in_progress` (step 4) and to `done`
(`verify`). The planner creates work-items.
`derived.ready` / `derived.wave` are engine-computed from `depends_on`
— never write them.

Each dispatch is recorded by the `in_progress` update of the
work-item (it carries `assignee` and `write_root`) and by a
`conductor:execution-report` (evidence verbatim). Write no
`conductor:assignment`. Executors take method / verify_command /
findings / constraints from `orchestra brief <task-slug>`. The brief
renders `## Orientation`: it quotes (verbatim, by id) work-item
Description/Approach, linked requirement text, design
Invariants/Assumptions, and named decisions. The dispatch prompt adds
territory and concurrency notes only. Do not paraphrase claims or
treat empty/legacy `criterion` as the lead claim.

Write a phase `score:position` only for a human-readable note. Phase
progress is derived from work-item states. The effort position still
changes at phase close.

## Steps

1. Run `orchestra handoff` if the handoff was not injected. Resolve
   **focus**. Read `orchestra view plan --effort <focus>` and blocking
   `continuity-question`s for that subject. Do not dispatch while a
   blocking question is open on this focus. A question with `scope`
   `plan-review:<phase-slug>` gates only that phase; clear on approve:

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   Do not dispatch another effort's tasks.

   Before planned ready work, re-dispatch retryable `in_progress`
   items (same executor mode) — see
   [retry-loop.md](references/retry-loop.md). Then continue with the
   planned ready list.
2. Select dispatchable work-items (plan view omits `derived.ready`/`wave`):

```bash
canon list --type score:work-item --state planned \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
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

   When `## Landing` is present, ensure branch `phase/<phase-slug>`
   from `main` and worktree `<repo>/.worktrees/<phase-slug>`:

```bash
git branch phase/<phase-slug> main
mkdir -p <repo>/.worktrees
git worktree add <repo>/.worktrees/<phase-slug> phase/<phase-slug>
```

   When Landing is present, code writes only under the worktree and
   store writes on the primary checkout (on `main`). `.canon`
   stays on that primary checkout. Task commits exclude `.canon`.
   When Landing is absent, a missing Landing section
   stays in the current checkout (incidental too); do not create a
   branch or worktree. When Landing is absent, execute does not
   create a `task/<phase-slug>/<task-slug>` branch. When Landing is
   absent, execute does not add a
   `<repo>/.worktrees/<phase-slug>--<task-slug>` worktree.
3. Group results by `derived.wave`. Lower waves first; waves stay
   serial. Re-run the step-2 `list` before each wave — wave numbers
   can shift.

   When Landing is present, at the start of a wave, execute
   creates branch `task/<phase-slug>/<task-slug>` from the current
   `phase/<phase-slug>` tip for every task in that wave except the
   work-item that depends_on every other phase work-item. When Landing
   is present, at the start of a wave, execute adds worktree
   `<repo>/.worktrees/<phase-slug>--<task-slug>` checked out on that
   task branch for every task in that wave except the work-item that
   depends_on every other phase work-item. execute does not
   create a task branch for the work-item that depends_on every other
   phase work-item. execute does not add a task worktree for the
   work-item that depends_on every other phase work-item. The
   work-item that depends_on every other phase work-item is dispatched
   in `<repo>/.worktrees/<phase-slug>` on `phase/<phase-slug>`.

   Re-dispatch of a task other than the work-item that depends_on
   every other phase work-item reuses branch
   `task/<phase-slug>/<task-slug>`. Re-dispatch of a task other than
   the work-item that depends_on every other phase work-item reuses
   worktree `<repo>/.worktrees/<phase-slug>--<task-slug>`. Before a
   re-dispatch continues, the parent merges `phase/<phase-slug>` into
   the task branch when the task branch does not already contain the
   phase tip. If that merge conflicts, leave it unresolved, open a
   blocking continuity question on the effort, and do not start the
   next wave (same conflict rules as wave end).

   Create the branch and worktree only when they are missing, and only
   for a task other than the work-item that depends_on every other
   phase work-item. On re-dispatch, reuse them. Run the merge only
   when the task branch does not already contain the phase tip:

```bash
git branch task/<phase-slug>/<task-slug> phase/<phase-slug>
git worktree add <repo>/.worktrees/<phase-slug>--<task-slug> task/<phase-slug>/<task-slug>
git -C <repo>/.worktrees/<phase-slug>--<task-slug> merge-base --is-ancestor phase/<phase-slug> HEAD \
  || git -C <repo>/.worktrees/<phase-slug>--<task-slug> merge phase/<phase-slug>
```

   Read `payload.executor` on each ready task (`inline` | `subagent`;
   missing/empty → `subagent`). If the wave disagrees, or any value is
   other than those two, stop and name the tasks — do not spawn or
   transition. Follow `## Approach` in the brief; do not ask the user
   for an implementation recipe when it is present.
4. When the wave agrees, transition each task to `in_progress` and set
   `assignee` (`inline` for inline; a short label for subagent) and
   `write_root` in the same update. `write_root` is the executor's
   write root. For a task other than the work-item that depends_on
   every other phase work-item, it is
   `<repo>/.worktrees/<phase-slug>--<task-slug>`. For the work-item
   that depends_on every other phase work-item, it is
   `<repo>/.worktrees/<phase-slug>` on `phase/<phase-slug>`. When
   Landing is absent, it is the current checkout. Work-item
   `payload.executor` is only the wave mode. Use
   `--expected-revision` from `list`/`get`:

```bash
canon update --type score:work-item --id <id> \
  --transition in_progress \
  --expected-revision <revision> \
  --payload '{"assignee":"<assignee>","write_root":"<write-root>"}'
```

   Print the brief. It quotes the work-item `## Description` and
   `## Approach`, each requirement by id, the phase design
   `## Invariants` / `## Assumptions`, and each named decision. Write
   no assignment record.

```bash
orchestra brief <task-slug>
```

   Write territory and concurrency notes for the dispatch prompt. The
   dispatch prompt names the write root. The dispatch prompt does not
   tell the executor to avoid `git add -A`. Do not restate
   `criterion`, `verify_command`, or findings — brief already has
   those.

   Unfrozen tdd tests can be written during execution. Record red through
   `orchestra check` before implementation, then green. Require explicit
   parent approval before changing method or oracle policy.

   If any active acceptance is **oracle-backed** (non-empty `test_ids`
   and `oracle_hashes`), list those frozen paths in the dispatch
   prompt and forbid editing them. Pushback → oracle amendment path
   below; never silently rewrite a frozen oracle. Add this section to
   the dispatch prompt, and omit it when no acceptance is
   oracle-backed:

```text
### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. Report proposed hash or test-id changes to the parent for oracle amendment approval.
For manifest claims:
An oracle hash or test-id change is a signed amendment in `.tuner/manifest.json`.
A non-zero exit means the acceptance is not done.
```

   **Oracle amendment (parent only):** every frozen hash change requires an
   approved `tuner:oracle-amendment` with hashes matching the green tree.
   The parent creates or supersedes that record with the acceptance subject,
   effort, phase, old_hashes, new_hashes, status approved, and Reason/Change.
   Executors never create or approve these records. Do not replace acceptance
   freeze fields. For manifest claims, Parent adds a signed amendment in `.tuner/manifest.json`, then:

```bash
orchestra verify verdict --cwd <repo-or-worktree> --at <revision> <claim-id>
```

   `<claim-id>` is that claim's `id` in `.tuner/manifest.json`.
   Exit 0 accepts; non-zero → acceptance not done; leave `in_progress`.

5. Dispatch by the shared `payload.executor`.

   **`subagent`:** one `generalPurpose` subagent per task, parallel
   within the wave. Give each only:

   - repo path — that write root
     (`<repo>/.worktrees/<phase-slug>--<task-slug>` for a task other
     than the work-item that depends_on every other phase work-item;
     `<repo>/.worktrees/<phase-slug>` on `phase/<phase-slug>` for that
     work-item; current checkout when Landing is absent) — plus task
     `subject`/title, `kind`, focus `effort`
   - the output of `orchestra brief <task-slug>` — verbatim
   - the territory notes from step 4, the frozen oracle paths when any
   - kind instruction:
     - `deliver` / `incidental` — implement (except verification task)
     - `repair` — reproduce, observe, name root cause if found, then fix
     - `evaluate` — run campaign; return metrics; do not "fix" unless
       requirement / verify_command says so
   - follow `## Approach`; do not ask for an implementation recipe
   - verification task (depends_on every other phase work-item): run
     phase checks; return `fail`; do not edit the tree
   - return the evidence block below; never call `canon`
     or edit `.canon/`

   **`inline`:** this session implements with the same brief,
   orientation, and kind instructions; still writes the
   execution-report and runs `verify` once in step 7. Same
   verification-task and Landing rules as subagent.

   With Landing, after each task's code lands and before verify, the
   parent does a commit per task so a passing check-run can carry a real
   SHA. The per-task commit for a task other than the work-item that
   depends_on every other phase work-item runs in that task worktree.
   That per-task commit stages with `git add -A` excluding
   `.canon`. That commit excludes `.canon`. Put that commit
   SHA in evidence `revision`. A passing check-run for a task other
   than the work-item that depends_on every other phase work-item
   records that task's commit as its revision. When a task other than
   the work-item that depends_on every other phase work-item has
   nothing to commit, execute does not create an empty commit.
   Skip when nothing to commit, no Landing, or the work-item that
   depends_on every other phase work-item. Subject `type(scope):
   summary` (`feat|fix|docs|refactor|test|chore`); body 1–2 sentences
   naming the task slug.

```bash
git -C <repo>/.worktrees/<phase-slug>--<task-slug> add -A -- . ':!.canon'
git -C <repo>/.worktrees/<phase-slug>--<task-slug> commit -m "$(cat <<'EOF'
feat(<scope>): <summary>

Land <task-slug> so a passing check-run can carry a real SHA.

EOF
)"
```

   Evidence block (subagent return or inline record):

   ```
   subject: <task-slug>
   kind: deliver | repair | evaluate | incidental
   result: pass | fail | blocked | abandoned
   revision: <git sha or "dirty">
   evidence: <what was run>
   observations: <repair/evaluate: what was seen>
   root_cause: <repair, if known>
   verdict: pass | fail | delta | inconclusive
   metrics: <evaluate: baseline vs candidate>
   claim: <evaluate/repair finding text, if any>
   needs_human: <true/false — if the verdict needs a maintainer call>
   attempted_action: <only if abandoned>
   retry_when: <only if abandoned>
   blocker: <only if blocked>
   ```

6. Mid-flight term changes (not status pings): message the subagent
   directly (it cannot read the store) and record the amendment,
   keyed to the work-item. Inline: record the same amendment and keep
   implementing:

```bash
canon create --type conductor:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","effort":"<focus>"}' \
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

   Then run `verify` here. verify for a task other than the
   work-item that depends_on every other phase work-item runs in that
   task worktree. It derives investigation / finding /
   check-run from this execution-report (not chat memory) and closes
   or leaves `in_progress`. `tdd`/`check` results come from
   `orchestra check` (verify runs it). Manual/review check-runs
   and the suite check-run (`orchestra suite record`, subject
   `<phase-slug>-suite`) stay parent writes.

   When the acceptance claim is in `.tuner/manifest.json`, run
   `orchestra verify verdict` before `done` (same command as step 4). Non-zero →
   leave `in_progress`.

   Do not supersede or re-derive readiness — dependents flip
   `derived.ready` when a dependency reaches terminal success; the
   next wave's `list` sees it.
8. At wave end, the parent merges each passing task branch of a task
   other than the work-item that depends_on every other phase
   work-item into `phase/<phase-slug>`. Run those merges in the phase
   worktree `<repo>/.worktrees/<phase-slug>`. Those wave-end merges
   run in task-slug order. The wave-end integration does not rebase
   the task branch. The parent does not merge a task branch whose
   check did not pass. Use `git merge` only.

```bash
git -C <repo>/.worktrees/<phase-slug> merge task/<phase-slug>/<task-slug>
```

   When a merge between a task branch and the phase branch conflicts,
   the parent leaves that conflict unresolved. When a merge between a
   task branch and the phase branch conflicts, the parent opens a
   blocking continuity question on the effort. Scope that question
   `merge:<task-slug>`. When a merge between a task branch and the
   phase branch conflicts, the parent does not start the next wave.
   Do not abort the merge. When both tasks can keep their behavior,
   edit the conflicted files in the phase worktree to keep both changes, stage them with `git add`
   and run `orchestra wave resolve <phase-slug> <task-slug>`. When the
   two tasks need competing behavior, leave the question open and ask
   the user.

```bash
canon create --type score:continuity-question \
  --subject "<focus>" \
  --payload '{"owner":"user","blocking":true,"scope":"merge:<task-slug>"}'
```

   Next wave only after every passing task branch in this wave has
   merged cleanly. After the last implementation wave's
   execution-reports, return to step 3 for the closing verification
   task (do **not** write an integration-report before verification).



## Record versus bind

Techniques and audit may record an unbound evidence-observation. It
does not earn a manifest claim. Path: claim id → evidence-binding →
evidence-observation. `orchestra verify bind` writes the
evidence-binding; then `orchestra verify recheck` before treating the
claim as earned. Inspect with `orchestra verify trail`.

```bash
orchestra verify trail --cwd <repo-or-worktree>
orchestra verify bind --cwd <repo-or-worktree> \
  --observation <evidence-observation-id> \
  --claim <claim-id> --base <base-rev> --head <head-rev>
orchestra verify recheck --cwd <repo-or-worktree> --claim <claim-id>
```

## Do not

- Write a plan document as authority
- Let subagents write records (any executor mode) — store is single-writer
- Restate `criterion` / verify_command / findings in the dispatch prompt, or
  paraphrase work-item / requirement claims — brief owns the quotes
- Write a `conductor:assignment`; the `in_progress` update carries
  `assignee` and `write_root`
- Write a phase `score:position` for progress; write one only for a
  human-readable note
- Skip `conductor:execution-report` and derive check-runs from chat memory
- Ask for an implementation recipe when `## Approach` is present
- Spawn a subagent for `inline`, or spawn when the wave disagrees on executor
- Dispatch when `derived.ready` is false, or another focus's work
- Write or recompute `ready`/`wave`
- Load the whole store; route by focus, then phase
- Close a phase whose phase-end gate does not hold (see phase-end.md)
- Write integration-report `pass` from a clean git merge alone, or write
  it before closing verification / reviewer, or invent its body
- Call the phase complete (or merge) without a proof-packet at phase-head
  when code or claims changed
- Merge without passing review at phase-head, or without required suite
  at phase-head when `suite.gate` is `required`
- Waive / skip / override configured suite policy in `orchestra.toml`
- Let the reviewer call `canon` or write `.canon`
- Re-run the reviewer more than once after fix tasks for the same phase-end
- Fix-and-rerun inside the suite step (`required` → fix tasks + re-run at
  new head; `advisory` → finding only)
- Create a branch or worktree without Landing; create a task branch or
  task worktree for the work-item that depends_on every other phase
  work-item; let code leave the worktree when Landing is present;
  write `.canon` off the primary checkout or include it in a task
  commit
- Skip the per-task commit when Landing is present and that task's
  code changed; create an empty commit when there is nothing to commit
- Rebase a task branch, merge a task branch whose check did not pass,
  resolve a task-branch merge conflict by any path other than
  `orchestra wave resolve`, or start the next wave while that conflict
  is unresolved
- Do not resolve a merge conflict outside `orchestra wave resolve`
- Do not push from phase close
- Tell the executor to avoid `git add -A`
- Let the verification executor edit the tree
- Reopen `done` — create a fix work-item and `depends_on` instead
- Re-dispatch after retry budget exhaustion without `scope: retry:<task-slug>`
- Skip the retryable `in_progress` pass
- Put a whole-suite command on a per-task `verify_command`
- Let an executor edit frozen oracle files or write
  `tuner:oracle-amendment`; or `create`/`correct` a task check-run
  with method `tdd`/`check` (those come from `orchestra check`). Suite
  (`orchestra suite record`) and `manual`/`review` stay parent writes
- Let a subagent sign an amendment or write `test_ids` / `oracle_hashes`


## Do not (moved from SKILL.md)

- Re-dispatch after retry budget exhaustion without `scope:
  retry:<task-slug>`; skip the retryable `in_progress` pass
- Put a whole-suite command on a per-task `verify_command`; let the
  reviewer call `canon`
