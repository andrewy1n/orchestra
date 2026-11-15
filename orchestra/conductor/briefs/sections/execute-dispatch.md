4. When the wave agrees, run `orchestra wave start {phase}`. It
   transitions each task in the lowest ready wave to `in_progress`.
   The same update sets `assignee`, `write_root`, a unique
   `dispatch_id`, and UTC `dispatch_started_at`. `write_root` is the
   executor's write root. For a task other than the work-item that
   depends_on every other phase work-item, it is
   `<repo>/.worktrees/{phase}--<task-slug>`. For the work-item
   that depends_on every other phase work-item, it is
   `<repo>/.worktrees/{phase}` on `phase/{phase}`. When Landing is
   absent, it is the current checkout. Work-item `payload.executor`
   is only the wave mode.

   `orchestra wave start` resolves one executor for the wave from its
   shape and project settings. A written `payload.executor` is an
   optional `inline` or `subagent` override. Stop before dispatch when
   any override is invalid or the overrides disagree. Use the resolved
   mode for every task in the wave.

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
     (`<repo>/.worktrees/{phase}--<task-slug>` for a task other
     than the work-item that depends_on every other phase work-item;
     `<repo>/.worktrees/{phase}` on `phase/{phase}` for that
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
git -C <repo>/.worktrees/{phase}--<task-slug> add -A -- . ':!.canon'
git -C <repo>/.worktrees/{phase}--<task-slug> commit -m "$(cat <<'EOF'
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
