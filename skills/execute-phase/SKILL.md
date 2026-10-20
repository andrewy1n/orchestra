---
name: execute-phase
description: >-
  Dispatches orchestra work-items whose derived.ready is true, in
  dependency order, each wave inline in this session or as one
  subagent per task, recording an assignment and execution-report
  per dispatch. Parent session writes records; subagents return
  evidence only. Use when the user asks to execute a phase, run
  ready work, or continue after engage.
---

# Execute the focused effort

Requires `adaptive-artifacts` and `orchestra` on PATH and a live
orchestra store. If missing,
follow [ensure-store.md](references/ensure-store.md) then `init` (if no goal
for the focus) and `plan-phase`. Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Follow `verify-work`
after each task finishes (subagent return or inline).

**Single-writer:** only this parent may write via `adaptive-artifacts`.
Subagents never write — including under any future `--read-only`
executor mode (that mode names what may be *read*; a subagent write
would race `--expected-revision`).

Task lifecycle is `planned -> in_progress -> done` (or `withdrawn`).
`derived.ready` / `derived.wave` are engine-computed from `depends_on`
— never write them.

Each dispatch is recorded: `project:assignment`, optional
`project:assignment-amendment`, then `project:execution-report`
(evidence verbatim). Executors take method / verify_command /
findings / constraints from the `project:brief` view — not from
retyping those into the assignment. The assignment's `## Orientation`
carries territory/concurrency notes and quotes (verbatim, by id)
work-item Description/Approach, linked requirement text, design
Invariants/Assumptions, and named decisions. Do not paraphrase claims
or treat empty/legacy `criterion` as the lead claim.

## Steps

1. `adaptive-artifacts hook-start` if views were not injected. Resolve
   **focus**. Read `project:plan` section `## <focus>` and blocking
   `continuity-question`s for that subject. Do not dispatch while a
   blocking question is open on this focus. A question with `scope`
   `plan-review:<phase-slug>` gates only that phase; clear on approve:

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   Do not dispatch another effort's tasks.

   Before planned ready work, re-dispatch retryable `in_progress`
   items (same executor mode) — see
   [retry-loop.md](references/retry-loop.md). Then continue with the
   planned ready list.
2. Select dispatchable work-items (plan view omits `derived.ready`/`wave`):

```bash
adaptive-artifacts list --type project:work-item --state planned \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --where derived.ready=true
```

   For `incidental`, drop `payload.phase` (it is `""`) and expect at
   most one result. `current-phase-slug` is the `project:phase` for
   this effort with `lifecycle_state` `in_progress` — never
   `current-position.payload.scope`. If none exist, stop and point to
   `plan-phase`. If several phases are `in_progress`, use the one
   named in context; ask if none is named.

   After plan review is answered and before the first wave, read
   `## Landing` from the phase body:

```bash
adaptive-artifacts get --type project:phase --id <phase-id>
```

   When `## Landing` is present, ensure branch `phase/<phase-slug>`
   from `main` and worktree `<repo>/.worktrees/<phase-slug>`:

```bash
git branch phase/<phase-slug> main
mkdir -p <repo>/.worktrees
git worktree add <repo>/.worktrees/<phase-slug> phase/<phase-slug>
```

   Code writes go in the worktree; store / `.artifacts` stay on the
   primary checkout (on `main`). Phase-branch commits exclude
   `.artifacts`. No Landing (or incidental) → stay in the current
   checkout; do not create a branch or worktree.
3. Group results by `derived.wave`. Lower waves first; waves stay
   serial. Re-run the step-2 `list` before each wave — wave numbers
   can shift.

   Read `payload.executor` on each ready task (`inline` | `subagent`;
   missing/empty → `subagent`). If the wave disagrees, or any value is
   other than those two, stop and name the tasks — do not spawn or
   transition. Follow `## Approach` in the brief; do not ask the user
   for an implementation recipe when it is present.
4. When the wave agrees, transition each task to `in_progress` and set
   `assignee` (`inline` for inline; a short label for subagent).
   Assignment `executor` is that assignee; work-item
   `payload.executor` is only the wave mode. Use `--expected-revision`
   from `list`/`get`:

```bash
adaptive-artifacts update --type project:work-item --id <id> \
  --transition in_progress \
  --expected-revision <revision> \
  --payload '{"assignee":"<assignee>"}'
```

   Regenerate the brief, then create the assignment. Orientation
   quotes only (copy, do not paraphrase):

   - work-item `## Description` and `## Approach`
   - each id in `requirements`: from specification `## Requirements`
     when present, else that id's line in the work-item Description
   - design `## Invariants` / `## Assumptions` when a phase design exists
   - each named decision's subject and `choice` when `decisions` is set

   Omit absent records. Do not restate `criterion`, `verify_command`,
   or findings — brief already has those.

   If any active acceptance is **oracle-backed** (non-empty `test_ids`
   and `oracle_hashes`), list those frozen paths in Orientation and
   forbid editing them. Pushback → oracle amendment path below; never
   silently rewrite a frozen oracle.

```bash
adaptive-artifacts list --type project:specification \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --state active --full

adaptive-artifacts list --type project:design \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --state active --full

adaptive-artifacts list --type project:decision \
  --where payload.effort=<focus> --state active --full

adaptive-artifacts view --id project:brief --out views/brief.md

adaptive-artifacts create --type project:assignment \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","executor":"<assignee>","effort":"<focus>"}' \
  --body "## Orientation

<territory split / concurrency warning / operational context>

### Work-item (quote)

<verbatim ## Description and ## Approach from the work-item>

### Requirements (quote by id)

<R1: … verbatim from specification or work-item Description>

### Design / decisions (quote)

<quoted design Invariants and Assumptions>

<quoted named decisions>

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done."
```

   Omit the Frozen oracle section when no acceptance is oracle-backed.

   **Oracle amendment (parent only):** do not edit the frozen file; do
   not `create`/`supersede` `project:oracle-amendment` or update
   acceptance `oracle_hashes`/`test_ids`. Parent adds a signed
   amendment in `.affidavit/manifest.json`, then:

```bash
aff verdict --cwd <repo-or-worktree> --at <revision> <claim-id>
```

   `<claim-id>` is that claim's `id` in `.affidavit/manifest.json`.
   Exit 0 accepts; non-zero → acceptance not done; leave `in_progress`.

5. Dispatch by the shared `payload.executor`.

   **`subagent`:** one `generalPurpose` subagent per task, parallel
   within the wave. Give each only:

   - repo path — worktree when Landing present, else current checkout —
     plus task `subject`/title, `kind`, focus `effort`
   - `## <task-slug>` from `views/brief.md` — verbatim
   - assignment `## Orientation` from step 4
   - kind instruction:
     - `deliver` / `incidental` — implement (except verification task)
     - `repair` — reproduce, observe, name root cause if found, then fix
     - `evaluate` — run campaign; return metrics; do not "fix" unless
       requirement / verify_command says so
   - follow `## Approach`; do not ask for an implementation recipe
   - verification task (depends_on every other phase work-item): run
     phase checks; return `fail`; do not edit the tree
   - return the evidence block below; never call `adaptive-artifacts`
     or edit `.artifacts/`

   **`inline`:** this session implements with the same brief,
   orientation, and kind instructions; still writes the
   execution-report and runs `verify-work` once in step 7. Same
   verification-task and Landing rules as subagent.

   With Landing, after code lands and before verify, commit on the
   phase branch from the worktree (exclude `.artifacts`); put the SHA
   in evidence `revision`. Skip when nothing to commit, no Landing, or
   verification task. Subject `type(scope): summary`
   (`feat|fix|docs|refactor|test|chore`); body 1–2 sentences naming
   the task slug.

```bash
git -C <repo>/.worktrees/<phase-slug> add -A -- . ':!.artifacts'
git -C <repo>/.worktrees/<phase-slug> commit -m "$(cat <<'EOF'
feat(<scope>): <summary>

Land <task-slug> so a passing check-run can cite this revision.

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
   directly (it cannot read the store) and record the amendment.
   Inline: record the same amendment and keep implementing:

```bash
adaptive-artifacts create --type project:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"assignment":"<task-slug>","effort":"<focus>"}' \
  --body "## Correction

<the correction, as sent to the executor>"
```

7. When the task finishes, the per-task Landing commit (step 5) must
   already exist before `verify-work`. Record the evidence block
   verbatim — it is the record, not raw material to cherry-pick:

```bash
adaptive-artifacts create --type project:execution-report \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","assignment":"<task-slug>","result":"<pass|fail|blocked|abandoned>","verdict":"<pass|fail|delta|inconclusive>","revision":"<git sha or dirty>"}' \
  --body "<the evidence block, verbatim>"
```

   Then run `verify-work` here. It derives investigation / finding /
   check-run from this execution-report (not chat memory) and closes
   or leaves `in_progress`. `tdd`/`check` results come from
   `orchestra check` (verify-work runs it). Manual/review check-runs
   and the suite check-run (`orchestra suite record`, subject
   `<phase-slug>-suite`) stay parent writes.

   When the acceptance claim is in `.affidavit/manifest.json`, run
   `aff verdict` before `done` (same command as step 4). Non-zero →
   leave `in_progress`.

   Do not supersede or re-derive readiness — dependents flip
   `derived.ready` when a dependency reaches terminal success; the
   next wave's `list` sees it.
8. Next wave. After the last implementation wave's execution-reports,
   return to step 3 for the closing verification task (do **not**
   write an integration-report before verification).

   When no same-focus `planned`/`in_progress` work-items remain (or
   incidental is closed), follow
   [phase-end.md](references/phase-end.md):

   closing verification → reviewer → integration-report → suite →
   phase gate → proof packet → Landing merge / phase close.

   An empty task list is not proof the phase is done. Skip
   reviewer/suite for incidental. Reopen later: kinds-and-focus,
   Closing and reopening.
9. Regenerate views (including `project:brief`); `adaptive-artifacts validate`.

## Record versus bind

Unbound evidence-observation does not earn a manifest claim.
Path: claim id → `aff bind` → evidence-observation; then `aff recheck`
before treating the claim as earned. Inspect with `aff trail`.

```bash
aff trail --cwd <repo-or-worktree>
aff bind --cwd <repo-or-worktree> \
  --observation <evidence-observation-id> \
  --claim <claim-id> --base <base-rev> --head <head-rev>
aff recheck --cwd <repo-or-worktree> --claim <claim-id>
```

## Do not

- Write a plan document as authority
- Let subagents write records (any executor mode) — store is single-writer
- Restate `criterion` / verify_command / findings in Orientation, or
  paraphrase work-item / requirement claims — quote by id; brief owns the rest
- Skip `project:execution-report` and derive check-runs from chat memory
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
  at phase-head when `phase_gate.suite.gate` is `required`
- Waive / skip / override contracted `phase_gate.suite` policy
- Let the reviewer call `adaptive-artifacts` or write `.artifacts`
- Re-run the reviewer more than once after fix tasks for the same phase-end
- Fix-and-rerun inside the suite step (`required` → fix tasks + re-run at
  new head; `advisory` → finding only)
- Create a branch/worktree without Landing; let code leave the worktree
  when Landing is present; write `.artifacts` off the primary checkout
  or include it in the phase-branch commit
- Skip the per-task phase-branch commit when Landing is present and code changed
- Push unless Landing names push as a human stop
- Let the verification executor edit the tree
- Reopen `done` — create a fix work-item and `depends_on` instead
- Re-dispatch after retry budget exhaustion without `scope: retry:<task-slug>`
- Skip the retryable `in_progress` pass
- Put a whole-suite command on a per-task `verify_command`
- Let an executor edit frozen oracle files; `create`/`supersede`
  `project:oracle-amendment`; or `create`/`correct` a task check-run
  with method `tdd`/`check` (those come from `orchestra check`). Suite
  (`orchestra suite record`) and `manual`/`review` stay parent writes
- Let a subagent sign an amendment or write `test_ids` / `oracle_hashes`
