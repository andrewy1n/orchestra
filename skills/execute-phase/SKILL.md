---
name: execute-phase
description: >-
  Dispatches affidavit work-items whose derived.ready is true, in
  dependency order, each wave inline in this session or as one
  subagent per task, recording an assignment and execution-report
  per dispatch. Parent session writes records; subagents return
  evidence only. Use when the user asks to execute a phase, run
  ready work, or continue after engage.
---

# Execute the focused effort

Requires `artifact-runtime` and a live affidavit store. If missing,
follow [ensure-store.md](../ensure-store.md) then `init` (if no goal
for the focus) and `plan-phase`. Follow
[kinds-and-focus.md](../kinds-and-focus.md). Follow `verify-work`
after each task finishes, whether a subagent returned or this
session just implemented it inline.

The git-filesystem backend is **single-writer**. Only this parent
session may call `adaptive-artifacts` in any form that writes.
Subagents never do — not now (they have no store access) and not once
a `--read-only` executor mode exists elsewhere in this project: that
mode names what an executor may *read*, it does not make the store
multi-writer, and a subagent write would race this session's
`--expected-revision`.

Task state is the work-item's lifecycle: `planned -> in_progress ->
done`, or `withdrawn`. Readiness (`derived.ready`) and wave
(`derived.wave`) are computed by the engine from the `depends_on`
graph at read time — this skill never writes either.

Each dispatch is recorded, not hand-transcribed: a `project:assignment`
for what an executor was handed, an optional `project:assignment-amendment`
for any mid-flight correction, and a `project:execution-report` for
what came back, verbatim. The `project:brief` view — not the
assignment body — is what tells an executor its acceptance method,
verify commands, findings, constraints, and position. An assignment
carries territory splits, concurrency warnings, and operational
orientation, and it quotes **original** work-item Description/Approach
and the requirement text for each linked id (verbatim, by id — do not
paraphrase the claim; do not treat empty or legacy `criterion` as the
lead claim). It also quotes the design Invariants and Assumptions and
the named decisions. Subagents return evidence and do not call
`adaptive-artifacts`.

## Steps

1. `adaptive-artifacts hook-start` if views were not injected. Resolve
   **focus**. Read `project:plan` section `## <focus>` and blocking
   `continuity-question`s for that subject. Do not dispatch while a
   blocking question is open on this focus. A question whose `scope`
   is `plan-review:<phase-slug>` is the plan review gate: it blocks
   only that phase, and the user clears it by approving the plan.
   When they approve, clear it at the event:

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   Do not dispatch another effort's tasks.

   Before selecting planned ready work, select retryable `in_progress`
   work-items in this phase and re-dispatch them (same executor mode).
   See **Retry loop** below. Only after that pass, continue with the
   planned ready list.
2. Select dispatchable work-items directly — `project:plan`'s rendered
   view does not carry `derived.ready`/`wave`, so query the store:

```bash
adaptive-artifacts list --type project:work-item --state planned \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --where derived.ready=true
```

   For `incidental`, drop the `payload.phase` filter (its work-item
   has `phase=""`) and expect at most one result. `current-phase-slug`
   is the subject of the `project:phase` record for this effort whose
   `lifecycle_state` is `in_progress` (`list --type project:phase
   --state in_progress --where payload.effort=<focus>`) — never
   `current-position.payload.scope`, which stays fixed per subject and
   does not track the phase. If none exist, stop and point to
   `plan-phase`. Several may be `in_progress` (one chat per phase):
   use the one named in context, and ask if none is named.

   After plan review is answered and before the first wave, read
   `## Landing` from the phase body:

```bash
adaptive-artifacts get --type project:phase --id <phase-id>
```

   When `## Landing` is present, create branch `phase/<phase-slug>`
   from base `main` if that branch is missing, and add the worktree
   `<repo-parent>/<repo-name>--<phase-slug>` if that path is missing.
   The primary checkout is the checkout that stays on `main` and
   receives store writes; it is not the phase worktree.

```bash
git branch phase/<phase-slug> main
git worktree add <repo-parent>/<repo-name>--<phase-slug> phase/<phase-slug>
```

   Inline work runs in that directory. Each subagent is given the
   worktree absolute path and code writes only under the worktree.
   The parent keeps store writes on the primary checkout and writes
   `.artifacts` only on the primary checkout. The phase branch commit
   excludes `.artifacts`.

   When the phase body has no Landing section, keep the current
   checkout and do not create a branch: a missing Landing section
   stays in the current checkout. Incidental work stays in the
   current checkout too.
3. Group the results by `derived.wave` (each result carries it).
   Do lower waves first; different waves stay serial. A wave number
   can shift between waves as earlier tasks finish — re-run the
   `list` above before each wave rather than trusting a wave computed
   earlier in this session.

   When dispatching a wave, read `payload.executor` on each ready
   task. Missing or empty means `subagent`. Resolve that before
   comparing. The values are `inline` and `subagent`. If the tasks
   in the wave disagree, stop and name them. Do not spawn anything.
   Do not transition those tasks. If `payload.executor` is set to
   anything other than `inline` or `subagent`, stop and name that
   task. Do not spawn anything.

   The brief already carries the work-item body. Follow `## Approach`
   in that body. Do not ask the user for an implementation recipe
   when `## Approach` is present. The parent remains the only writer.
4. When the wave agrees on one executor, transition each task about
   to dispatch to `in_progress` and set `assignee`. For `subagent`,
   `assignee` is a short subagent label. For `inline`, `assignee` is
   `inline`, because this session runs the task. The assignment's
   `executor` is that assignee — who was handed the work — while the
   work-item's `payload.executor` is only the wave mode. Fetch
   `--expected-revision` from the `list`/`get` output:

```bash
adaptive-artifacts update --type project:work-item --id <id> \
  --transition in_progress \
  --expected-revision <revision> \
  --payload '{"assignee":"<assignee>"}'
```

   Regenerate the brief so it is current for this dispatch, then
   record the assignment. Its `## Orientation` body carries territory
   splits between concurrent executors, concurrency warnings, and
   operational orientation (paths, sandbox, tooling quirks). It also
   quotes original record text: the work-item `## Description` and
   `## Approach` (verbatim), the requirement text for each id in the
   work-item's `requirements`, the phase design's Invariants and
   Assumptions, and the named decisions in the work-item's
   `decisions`. Read those records and copy the text into the
   orientation — do not paraphrase. The executor receives that body
   and does not call `adaptive-artifacts`.

   Quote the work-item Description and Approach from the work-item
   body itself. When `requirements` is set, quote each listed id's
   text from the phase `project:specification` `## Requirements`
   section when one exists; when there is no specification, quote
   that id's line from the work-item `## Description`. When a
   `project:design` exists for the phase, quote its `## Invariants`
   and `## Assumptions`. When `decisions` is set, quote each named
   decision's subject and `choice`. When those records or fields are
   absent, omit the quotes. Do not restate `criterion`,
   `verify_command`, or finding text, and do not invent a claim from
   criterion — that is what the brief view is for (method /
   verify_command / findings), and copying or paraphrasing creates a
   second, staleness-prone copy of the same fact.

   When any of this work-item's active acceptances are **oracle-backed**
   (non-empty `test_ids` and `oracle_hashes`), the Orientation must
   list the frozen oracle file paths from `oracle_hashes` and forbid
   the executor from editing those files. Frozen oracle hashes are
   close authority; the executor may change production code, not the
   frozen oracle files. If the executor needs a different oracle
   (pushback), stop editing and use the **oracle-amendment** path
   below — do not silently rewrite a frozen oracle file.

```bash
adaptive-artifacts list --type project:specification \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --state active --full

adaptive-artifacts list --type project:design \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug> \
  --state active --full

adaptive-artifacts list --type project:decision \
  --where payload.effort=<focus> --state active --full
```

```bash
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
Do not edit them. Pushback → oracle-amendment (parent approves)."
```

   Omit the Frozen oracle section when no acceptance on this task is
   oracle-backed.

### Oracle amendment (parent only)

When an executor (or this session on `inline`) cannot satisfy a
requirement without changing a frozen oracle file: do not edit that
file. Create a `project:oracle-amendment` with `status` `requested`,
then the parent alone approves or rejects.

```bash
adaptive-artifacts create --type project:oracle-amendment \
  --subject "<task-slug>" \
  --payload '{"acceptance":"<acceptance-record-id>","effort":"<focus>","phase":"<current-phase-slug>","old_hashes":"<relpath:sha256:hex from acceptance oracle_hashes>","new_hashes":"<relpath:sha256:hex after proposed oracle edit>","status":"requested"}' \
  --body "## Reason

<why the frozen oracle must change>

## Change

<what changes in the oracle file(s) and why it still witnesses the requirement>"
```

   On parent approval, supersede to `status` `approved` and update the
   acceptance freeze fields (`oracle_hashes`, and `test_ids` /
   `verify_command` when those change). On reject, supersede to
   `status` `rejected` and leave freeze fields unchanged. Only the
   parent writes freeze fields and amendments.

```bash
adaptive-artifacts supersede --type project:oracle-amendment --id <amendment-id> \
  --expected-revision <revision> \
  --payload '{"status":"approved"}'

adaptive-artifacts update --type project:acceptance --id <acceptance-id> \
  --expected-revision <revision> \
  --payload '{"oracle_hashes":"<new_hashes matching the approved amendment>","test_ids":"<updated node ids if any>","verify_command":"python3 -m pytest <updated-node-ids> -q"}'
```

5. Dispatch the wave by that shared `payload.executor`.

   `subagent` keeps the current dispatch: one `generalPurpose`
   subagent per task, in parallel within the wave (`Task` /
   `generalPurpose`). Give each only:

   - repo path — the worktree absolute path
     `<repo-parent>/<repo-name>--<phase-slug>` when `## Landing` is
     present, otherwise the current checkout — task `subject` /
     title, `kind`, focus `effort`
   - the `## <task-slug>` section of `views/brief.md` (work-item body,
     acceptance, findings, constraints, position, and any prior
     amendments) — verbatim, not retyped
   - the assignment's `## Orientation` body from step 4
   - kind-specific instruction:
     - `deliver` / `incidental` — implement the change, except a
       verification task, which does not implement a fix
     - `repair` — reproduce, record observations, name a root cause
       if found, then fix; do not skip diagnose
     - `evaluate` — run the campaign; return metrics / comparison;
       do not "fix" the system unless the requirement /
       verify_command says so
   - follow `## Approach` in the work-item body; do not ask the user
     for an implementation recipe when that section is present
   - when the task is the verification task (the work-item that
     `depends_on` every other phase work-item), run the phase checks
     and do not implement a fix. The verification executor returns
     `fail` and does not edit the tree.
   - subagents return evidence and do not call `adaptive-artifacts`.
     That holds for any form that writes, and it still holds once a
     `--read-only` mode exists for executors; do **not** edit
     `.artifacts/`; return the evidence block below

   `inline` does not spawn a subagent. This session implements the
   task, then still writes the execution-report and runs
   `verify-work` in step 7 — not twice. When the task is the
   verification task, do not implement a fix. The verification
   executor returns `fail` and does not edit the tree. When `## Landing` is
   present, that implementation runs in the worktree. Use the same
   brief section,
   orientation, and kind-specific instruction a subagent would have
   been given. Follow `## Approach`. Fill the evidence block below
   in this session.

   When `## Landing` is present, after each task's code lands and
   before verify for that task, the executor commits on the phase
   branch from the worktree. That commit excludes `.artifacts`. A
   commit per task so a passing check-run can carry a real SHA.
   Put the resulting SHA in the evidence `revision`. Skip the
   per-task commit when there is nothing to commit, when `## Landing`
   is absent, or when the task is the verification task (it does not
   edit the tree).

```bash
git -C <repo-parent>/<repo-name>--<phase-slug> add -A -- . ':!.artifacts'
git -C <repo-parent>/<repo-name>--<phase-slug> commit -m "<task-slug>"
```

   Evidence block (what a subagent returns, or what this session
   records after an inline task):

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

6. If the assignment's terms turn out wrong or incomplete while a
   `subagent` task is still working — a change to what it was told,
   not a status ping — send the correction to that subagent directly
   (it cannot read the store to pick up a change) and record it, so
   it survives past the chat transcript. An `inline` task has no
   separate executor to message; record the same amendment if the
   terms change, and keep implementing in this session:

```bash
adaptive-artifacts create --type project:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"assignment":"<task-slug>","effort":"<focus>"}' \
  --body "## Correction

<the correction, as sent to the executor>"
```

7. When a subagent returns, or when this session finishes an
   `inline` task, the per-task commit on the phase branch (step 5,
   when Landing is present) must already have landed before
   `verify-work`. Record the evidence block before judging it. That
   block is the record, not raw material for this session to
   hand-pick fragments from:

```bash
adaptive-artifacts create --type project:execution-report \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","assignment":"<task-slug>","result":"<pass|fail|blocked|abandoned>","verdict":"<pass|fail|delta|inconclusive>","revision":"<git sha or dirty>"}' \
  --body "<the evidence block, verbatim>"
```

   Then run `verify-work` in this parent. It derives
   `investigation-observation` / `finding` / `check-run` records from
   this execution-report — not from this session's memory of the chat
   — and transitions the work-item to `done` or `withdrawn`, or leaves
   it `in_progress` on fail/blocked. Do not supersede or re-derive
   anything yourself — a dependent task's `derived.ready` flips to
   `true` automatically the moment its dependency's lifecycle reaches
   its terminal success state; the next wave's `list` in step 3 will
   see it.
8. Next wave. Phase-end order for structured work with Landing:

   last implementation wave → closing verification → reviewer →
   integration-report from the reviewer `integration` section →
   suite (per `phase_gate.suite` policy) → phase gate (acceptances@head +
   review@head + suite@head when gate=required) → Landing merge.

   The verification task is the work-item that `depends_on` every
   other phase work-item. An implementation wave is a dispatch wave
   of the other work-items. After the last implementation wave's
   execution-reports are recorded, return to step 3 and dispatch the
   closing verification task (do **not** write an integration-report
   before verification — that content comes from the reviewer below).

   After the closing verification task succeeds (`done`), and before
   merge, run the phase-end reviewer once, then the contracted suite.
   Skip the reviewer, review check-run, integration-report, and suite
   when incidental.

   Parent only — the reviewer writes no store records:

   1. Build the restricted brief with `orchestra.reviewer.build_reviewer_brief`
      (work-item descriptions/Approach, acceptances, requirements/
      invariants, and `git diff <base>..<phase-head>` only — no
      execution-report, check-run, assessment, or assignment text).
   2. Dispatch `agents/se-reviewer.md` (Cursor: tightest read-only /
      explore restriction available + the agent prompt forbid). Refuse
      any reviewer-authored store write or tree mutation.
   3. Parse the structured verdict. Create one `project:check-run` with
      `method: review`, `evidence_kind: review`, `revision` = phase
      head, `result` from the verdict (`PASS` → `pass`, `NEEDS_WORK` →
      `fail`). Create one `project:finding` per NEEDS_WORK item
      (`needs: none` when a fix task is created, `needs: human` for
      `severity: judgment` or when no fix is created).

```bash
adaptive-artifacts create --type project:check-run \
  --subject "<phase-slug>-review" \
  --payload '{"criterion_id":"<phase-review-acceptance-id>","revision":"<phase-head-sha>","result":"<pass|fail>","effort":"<focus>","method":"review","signed_by":"","evidence_kind":"review"}' \
  --body "<reviewer output, verbatim>"

adaptive-artifacts create --type project:finding \
  --subject "review-<task-or-phase>-<kind>" \
  --payload '{"claim":"<kind> on <task>: <expected>","basis":"<observed>","invalidated_when":"fix lands and reviewer re-run passes, or human clears","effort":"<focus>","needs":"<none|human>"}' \
  --body "## Evidence

<expected vs observed from the finding>

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Create a fix work-item under the retry budget, or answer Needs you."
```

   4. Fixable NEEDS_WORK kinds (`spec-gap`, `behavior-bug`,
      `missing-test`, `invariant-violation`, except `severity:
      judgment`) become fix work-items via the **Retry loop** Fix tasks
      path and `retry_max_fix_tasks` budget. Never reopen `done`.
      After those fixes land and are verified, re-run the reviewer
      **once** on the new phase diff (same brief rules). Do not re-run
      a second time. When the fix-task budget is exhausted, escalate
      with the budget-exhaustion Needs-you path (`continuity-question`
      / finding `needs: human`) and stop — do not reopen `done`.
   5. Write one `project:integration-report` for the phase whose body
      sections come from the reviewer's `integration` map (parent still
      creates the record). Skip the report when incidental, or when no
      implementation wave has more than one task. `result` is `pass`,
      `fail`, or `blocked`. Write `pass` only when the reviewer
      verdict is `PASS` and those sections hold. A clean git merge does
      not by itself write `pass`.

```bash
adaptive-artifacts create --type project:integration-report \
  --subject "<phase-slug>" \
  --payload '{"phase":"<phase-slug>","effort":"<focus>","result":"<pass|fail|blocked>","revision":"<phase-head-sha>"}' \
  --body "## Interfaces

<from reviewer integration.interfaces>

## Assumptions

<from reviewer integration.assumptions>

## Invariants

<from reviewer integration.invariants>

## Conflicts

<from reviewer integration.conflicts>"
```

   On integration-report `fail` or `blocked`, or when the review
   check-run is not a passing `method: review` at the phase head, do
   not merge. Leave the phase `in_progress` and stop (or route fixes /
   escalate as above).

   After the reviewer passes (and the integration-report is written),
   honor the contracted **suite** policy once before the merge gate.
   Parent only. Agents must **not** waive suite policy — do not skip,
   soften, or override `phase_gate.suite`; change the project design
   (contract) instead. Load policy with `orchestra.suite.load_suite_policy`
   (same project-design path resolution as other project metadata).
   Missing `phase_gate.suite` or `mode=none` → skip the suite step.
   `mode=external` or `gate=deferred` → do **not** run locally.
   `gate=deferred` is a Landing human stop (ask before merge; do not
   invent a local pass). When `mode` is `smoke` or `full` and a
   `command` is set, start a detached tmux window in the phase
   worktree running that contracted command (not a per-task
   `verify_command`), poll/reattach for completion, then record
   **one** `project:check-run` at the phase-head SHA. Subject is
   `<phase-slug>-suite`; `evidence_kind` is `integration`; include
   runner metadata (`revision`, `exit_code`, `duration_s`,
   `output_sha256`, and `failing_node_ids` when failed). Use
   `orchestra.suite` (`start_suite_background`, `poll_suite` /
   `collect_suite`, `record_suite_check_run`). Dirty-only pass is
   refused the same way as `aff check` (commit first, or
   `--allow-dirty` → `revision=dirty` + `diff_sha256`). The phase
   suite is never red-first (red-first stays `method: tdd` only).

   Gate behavior after the check-run (when a local run happened):
   - `gate=required` — missing or failing suite at the phase head
     blocks Landing merge. On `fail`, create fix work-item(s) under
     the **Retry loop** fix-task budget, clustered by failing test
     file/module (one fix subject per module). Never reopen `done`.
     No inline fix-and-rerun. After fixes land and are verified,
     re-run the suite at the new phase head. When the fix-task
     budget is exhausted, escalate with the budget-exhaustion
     Needs-you path and stop.
   - `gate=advisory` — record the check-run; on `fail` also create a
     `project:finding` (advisory suite fail). Do **not** block merge
     and do **not** create required-gate fix-task storms.
   - `gate=deferred` — no local run; Landing human stop.

   If the tmux job is orphaned, reattach with
   `tmux attach -t se-suite-<phase-slug>` (or inspect the log / exit
   files under the worktree `.suite/`), then re-start the suite in
   the phase worktree if the session is gone. Do **not** fix-and-rerun
   inside this verification step.

```bash
adaptive-artifacts create --type project:check-run \
  --subject "<phase-slug>-suite" \
  --payload '{"criterion_id":"<phase-slug>-suite","revision":"<phase-head-sha>","result":"<pass|fail|blocked>","effort":"<focus>","method":"check","signed_by":"","evidence_kind":"integration","runner":"affidavit","exit_code":0,"duration_s":0,"output_sha256":"<digest>","failing_node_ids":"[]"}' \
  --body "<suite output tail; failing node ids when failed>"
```

```bash
adaptive-artifacts create --type project:finding \
  --subject "suite-advisory-<phase-slug>" \
  --payload '{"claim":"advisory suite fail for <phase-slug>-suite","basis":"<exit_code and failing node ids>","invalidated_when":"suite check-run passes at phase head, or human clears","effort":"<focus>","needs":"none"}' \
  --body "## Evidence

<suite output tail>

## Consequence

Advisory only — Landing is not blocked by this suite fail.

## Follow-up

Fix opportunistically or clear the finding; do not open a required-gate fix-task storm."
```

   When no `planned`/`in_progress` same-focus work-items
   remain in this phase (or the incidental task is closed), check the
   phase gate before closing anything. An empty task list is not proof
   the phase is done:

```bash
adaptive-artifacts list --type project:work-item \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

adaptive-artifacts list --type project:acceptance \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

adaptive-artifacts list --type project:check-run \
  --where payload.criterion_id=<acceptance-id> --order-by recorded_at

adaptive-artifacts list --type project:check-run \
  --where payload.method=review --where payload.effort=<focus> \
  --order-by recorded_at

adaptive-artifacts list --type project:check-run \
  --where payload.evidence_kind=integration --where payload.effort=<focus> \
  --order-by recorded_at
```

   The gate holds only when all of these are true:
   - The phase's verification task (the work-item that `depends_on`
     every other phase work-item) exists and is `done`.
   - Every active phase acceptance has a check-run, and the latest
     check-run per `criterion_id` has a passing `result`.
   - Every active phase acceptance has a passing runner check-run
     whose `revision` is the phase-head SHA.
   - Every `method=manual` latest check-run has `signed_by` set.
   - A passing `method: review` / `evidence_kind: review` check-run
     exists whose `revision` is the phase-head SHA (required before
     merge; skip this bullet for incidental).
   - When `phase_gate.suite.gate` is `required` (and mode is not
     `none`), a passing suite check-run (`subject` `<phase-slug>-suite`,
     `evidence_kind: integration`) exists whose `revision` is that
     same phase-head SHA. Missing or failing suite blocks merge.
     When gate is `advisory`, suite fail does not block. When gate is
     `deferred` or mode is `none`, skip this bullet. (Skip for
     incidental.)

   When the user signs an unsigned manual check, clear it at the event
   (kinds-and-focus, Needs-you clears):

```bash
adaptive-artifacts correct --type project:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

   If the gate does not hold, leave the phase `in_progress`. Tell the
   user which criterion has no check-run, a failing latest check-run,
   or no signature, that the verification task is missing, that the
   phase lacks a passing review check-run at the phase head, or that
   a required suite is missing or failing at the phase head. Then
   stop. Do not close the phase to move on. `deliver` and `repair`
   phases always need the verification task and a passing review at
   head; a passing suite at head is required only when
   `phase_gate.suite.gate` is `required`. Skip the gate for incidental
   work. Do not waive suite policy to force a close.

   When the gate holds and `## Landing` is present, commit the phase
   branch from the worktree. That commit excludes `.artifacts`. From
   the primary checkout, merge into `main`, then commit the store on
   `main`. The store commit on the primary checkout follows the phase
   close below. When Landing names push as a human stop, stop before
   pushing and ask. Push only as a human stop: push only when it is a
   human stop. Otherwise do not push. When `## Landing` is absent,
   skip the branch commit, the merge, and the store commit.

```bash
git -C <repo-parent>/<repo-name>--<phase-slug> add -A -- . ':!.artifacts'
git -C <repo-parent>/<repo-name>--<phase-slug> commit -m "<phase-slug>"
git -C <primary-checkout> merge phase/<phase-slug>
```

   Then close the phase, close its phase position
   (`subject` = phase slug) with `status: closed`, and update the
   effort position narrative (`subject` = focus). `current-position.scope`
   is a stable per-subject value — never change it here, and never put
   the next phase's slug into it; `supersede` rejects a successor whose
   `scope` differs from the predecessor's ("breaks identity
   continuity"). `phase` is a required payload reference to a real
   `project:phase` subject — set it to the next phase this narrative
   names, but that is a pointer, not the authority: which phase is
   current is still derived by querying `project:phase` state, not
   read off this record:

```bash
adaptive-artifacts update --type project:phase --id <phase-id> \
  --transition done --expected-revision <revision>

adaptive-artifacts supersede --type project:current-position --id <phase-position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

adaptive-artifacts supersede --type project:current-position --id <effort-position-id> \
  --expected-revision <revision> \
  --payload '{"position":"<phase-slug> done; next up: <next-phase-slug>","scope":"<unchanged from predecessor>","effort":"<focus>","phase":"<next-phase-slug>"}'
```

   Then commit the store on `main` from the primary checkout, only
   when `## Landing` was present:

```bash
git -C <primary-checkout> add -- .artifacts
git -C <primary-checkout> commit -m "<phase-slug> store"
```

   Skip all three for incidental. Also skip the phase-branch commit,
   the merge, and the store commit for incidental. Another chat may
   have just closed a different phase; on a revision conflict,
   re-read the effort position
   and retry. Do **not** materialize the next phase's
   tasks unless the user asks (`plan-phase` promotes it). Do not touch
   other subjects.

   If no `planned` or `in_progress` phase is left for this effort, ask
   the user whether more phases follow. If yes, stop; `plan-phase`
   adds the next one. If no, close the effort: supersede its goal and
   position with `status: closed` (`supersede` merges the payload, so
   the other fields carry over). Closed efforts drop out of handoff,
   brief and the dashboard:

```bash
adaptive-artifacts supersede --type project:active-goal --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

adaptive-artifacts supersede --type project:current-position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'
```

   To reopen an effort later, see kinds-and-focus, Closing and
   reopening.
9. Regenerate views (including `project:brief`); `adaptive-artifacts validate`.

## Retry loop

Parent-only. Do this at the start of each dispatch cycle, before the
planned ready `list` in step 2. Evidence escalation still chooses
`level` / `next`; the budget only decides when to stop.

### Re-dispatch selection

```bash
adaptive-artifacts list --type project:work-item --state in_progress \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug>
```

For each result, load the latest `project:assessment` for that task
(structured) or the latest `project:check-run` (simple). Treat as
retry when the assessment has `next` `execute`, or the check-run has
`result` `fail`. Skip a task whose executor is still running for the
current assignment. Skip a task with an open blocking
`continuity-question` whose `scope` is `retry:<task-slug>`.

Re-dispatch with the same `payload.executor` mode as the prior wave
(`inline` or `subagent`; missing means `subagent`). Do not change the
wave mode for a retry.

### Budget (hard backstop)

Defaults (override in the phase body's run facts):

- `retry_max_redispatches`: 2 re-dispatches per task
- `retry_time_multiplier`: 2 (stop when cumulative executor running
  time ≥ 2× `estimate_minutes` when that field is set; whichever of
  count or time comes first)
- `retry_max_fix_tasks`: 3 fix work-items created for the phase

When run facts omit a key, use the default. When cumulative time
cannot be computed from assignment / execution-report timestamps,
fall back to the re-dispatch count only. `attempts` is the
re-dispatch count (optional integer; treat absent as 0). The evidence
ladder is unchanged for routing.

When a per-task or per-phase fix-task budget is exhausted, do not
re-dispatch that task. Open Needs you and stop selecting it:

```bash
adaptive-artifacts create --type project:continuity-question \
  --subject "<focus>" \
  --payload '{"owner":"user","blocking":true,"scope":"retry:<task-slug>"}'

adaptive-artifacts create --type project:finding \
  --subject "retry-<task-slug>" \
  --payload '{"claim":"retry budget exhausted for <task-slug> after <attempts> re-dispatches","basis":"<attempts, check-runs, assessments>","invalidated_when":"human raises the budget or withdraws the task","effort":"<focus>","needs":"human"}' \
  --body "## Evidence

<attempts, failing check-runs, latest assessment>

## Consequence

Dispatch of this task stops until the human answers.

## Follow-up

Raise the run-fact budget, withdraw the task, or choose another approach."
```

When the user answers the question or clears the finding, clear each
at the event (kinds-and-focus, Needs-you clears):

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>

adaptive-artifacts update --type project:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

### Amendment, attempts, re-dispatch

For each retryable task still inside budget: record an
`assignment-amendment` whose `## Correction` quotes the failing
check-run evidence (runner output tail) and the assessment's
`## Reason` when present; increment `attempts`; then create a fresh
`project:assignment` and dispatch as in steps 4–5 (same executor
mode). The work-item stays `in_progress` — do not reopen `done`.

```bash
adaptive-artifacts create --type project:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"assignment":"<task-slug>","effort":"<focus>"}' \
  --body "## Correction

Re-dispatch after failure.

## Failing check-run

<runner output tail from the failing check-run>

## Reason

<assessment ## Reason when present, else omit>"

adaptive-artifacts update --type project:work-item --id <id> \
  --expected-revision <revision> \
  --payload '{"attempts":1}'

adaptive-artifacts create --type project:assignment \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","executor":"<assignee>","effort":"<focus>"}' \
  --body "## Orientation

Re-dispatch attempt <attempts>. Same territory and executor mode as the prior wave.

<quoted work-item Description/Approach, requirement texts by id, design, and decisions as in step 4>"
```

Set `attempts` to the prior value plus one (absent means 0, so the
first re-dispatch writes `1`). Then dispatch with that same executor
mode and continue through execution-report + `verify-work`.

### Fix tasks (closing verification)

When the closing verification task (the work-item that `depends_on`
every other phase work-item) fails and the cause is another task's
code, create a new fix work-item in the same phase — never reopen
`done`. The fix has no `depends_on`. Its Approach comes from the
failure; its acceptance is the failing check. Then add a `depends_on`
edge from the verification task to the fix so `derived.ready`
re-gates verification. Count the new fix against
`retry_max_fix_tasks`. If that phase budget is exhausted, use the
budget-exhaustion Needs-you path above (`scope: retry:<verification-slug>`
or `retry:<fix-slug>` as appropriate) instead of creating another fix.

```bash
adaptive-artifacts create --type project:work-item \
  --subject "fix-<failing-area>" \
  --payload '{"title":"Fix <failing area>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<focus>","executor":"<same mode as phase wave>","size":"S","estimate_minutes":8,"requirements":"<ids>","decisions":"<ids>"}' \
  --body "## Description

Fix the failure that blocked closing verification.

## Approach

<from the failing check-run / node ids>"

adaptive-artifacts create --type project:acceptance \
  --subject "fix-<failing-area>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<focus>","verify_command":"<command>","requirement":"<id>"}'

adaptive-artifacts update --type project:work-item --id <verification-work-item-id> \
  --expected-revision <revision> \
  --rel depends_on:<fix-work-item-id>
```

Never transition a `done` work-item back to `in_progress` or
`planned`. Fix tasks stay in the current phase.

## Do not

- Write a plan document as authority
- Let subagents create/supersede/transition records, in any current or
  future executor mode — the store is single-writer regardless of what
  an executor is allowed to read
- Restate `criterion`, verify commands, or finding text inside an
  assignment's `## Orientation`, or paraphrase the work-item /
  requirement claim — quote Description/Approach and requirement
  texts by id verbatim; brief already carries method /
  verify_command / findings, and a paraphrase goes stale
- Skip the `project:execution-report` and derive check-runs straight
  from chat memory of what a subagent or this session reported
- Ask the user for an implementation recipe when `## Approach` is
  present
- Spawn a subagent for an `inline` task, or spawn anything when the
  wave's tasks disagree on `payload.executor`
- Dispatch a work-item whose `derived.ready` is `false`, or another
  focus's work
- Write or recompute `ready`/`wave` — they are derived; re-query them
- Load the whole store; route by focus, then phase
- Close a phase whose gate in step 8 does not hold
- Write `pass` on `project:integration-report` because a git merge was
  clean. A clean git merge does not by itself write `pass`
- Write the integration-report before closing verification / the
  reviewer, or invent its body instead of copying the reviewer's
  `integration` section
- Merge (or close the phase) without a passing `method: review`
  check-run at the phase-head SHA
- Merge (or close the phase) without a passing suite check-run
  (`<phase-slug>-suite`, `evidence_kind: integration`) at the
  phase-head SHA when `phase_gate.suite.gate` is `required`
- Waive, skip, or override contracted `phase_gate.suite` policy
  (mode/command/gate). Agents enforce the design; only a contract
  edit changes it
- Let the reviewer call `adaptive-artifacts` or write `.artifacts`
- Re-run the reviewer more than once after fix tasks for the same
  phase-end pass
- Fix-and-rerun inside the suite verification step (for `gate=required`,
  create fix work-items under the retry budget instead; rerun suite
  at the new head after fixes; for `gate=advisory`, record finding
  only — no fix-task storm)
- Create a branch or worktree when the phase body has no Landing section
- Let code writes leave the worktree when `## Landing` is present
- Write `.artifacts` anywhere but the primary checkout, or include
  `.artifacts` in the phase branch commit
- Skip the commit per task on the phase branch when `## Landing` is
  present and the task changed code — verify needs a real SHA
- Push unless Landing names push as a human stop
- Let the verification executor edit the tree. The verification
  executor returns `fail` and does not edit the tree.
- Reopen a `done` work-item. Never reopen `done`; create a fix
  work-item and `depends_on` instead
- Re-dispatch a task after its retry budget is exhausted without
  opening `scope: retry:<task-slug>` Needs you
- Skip the retryable `in_progress` pass and only select `planned`
  ready work
- Put a whole-suite command on a per-task `verify_command` — per-task
  checks stay scoped; the suite is the phase-level
  `phase_gate.suite` run
- Let an executor edit a frozen oracle file listed in
  `oracle_hashes`. Pushback uses `project:oracle-amendment`
  (`requested` → parent `approved` / `rejected`); parent alone
  updates freeze fields
- Let a subagent create or approve oracle-amendments, or write
  `test_ids` / `oracle_hashes` — parent only
