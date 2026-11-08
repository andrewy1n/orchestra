# Phase end

Parent-only. Run after the closing verification task is `done`, when
no same-focus `planned`/`in_progress` work-items remain (or the
incidental task is closed). Order:

last implementation wave → closing verification → analyze → suite (per
`[suite]` in `orchestra.toml`) → reviewer → integration-report from
reviewer `integration` → phase gate → phase close.

After the last implementation wave's execution-reports, return to
execute step 3 for the closing verification task. Do **not**
write an integration-report before verification.

Skip reviewer / review check-run / integration-report / suite when
incidental. An empty task list is not proof the phase is done — check
the gate below before closing.

## Analyze

After the closing verification is `done` and before the reviewer, run:

```bash
orchestra analyze <phase-slug> --stage close
```

Refuse to start the reviewer while it exits 1. Fix each error finding
first, then run it again.

## Suite

After analyze exits 0 and before the reviewer starts. The suite runs at
the phase head, so the review and the suite name the same revision. Do not
waive suite policy — a human changes `[suite]` in the root
`orchestra.toml` instead. Load with `orchestra suite policy`. An omitted
`[suite]` section or `mode=none` → skip.
`mode=external` or `gate=deferred` → do not run locally (`deferred` =
Landing human stop). For `smoke`/`full` with a `command`: run via
`orchestra suite start` / `poll` / `collect` / `record` in the phase
worktree (tmux); one check-run at phase-head SHA, subject
`<phase-slug>-suite`, `evidence_kind: integration`, with runner
metadata. Dirty-only pass refused like `orchestra check`. Suite is
never red-first.

After a local run:

- `gate=required` — missing/failing suite blocks merge. On fail, fix
  work-items under retry budget (one subject per failing module);
  never reopen `done`; no inline fix-and-rerun; re-run suite at new
  head after fixes; budget exhausted → Needs you. Create the fix
  work-items before the reviewer starts. The reviewer never sees a head
  with a failing required suite.
- `gate=advisory` — record check-run; on fail also a finding; do not
  block merge; no fix-task storm.
- `gate=deferred` — no local run; Landing human stop.

When the suite fails, re-run each failing test id in a clean `main`
worktree. Label every id `new` or `pre-existing` in the check-run basis
or finding. A `pre-existing` label does not change the gate: `required`
still blocks and `advisory` still does not. Put the pre-existing ids in
front of the user; do not wait silently.

Orphaned tmux: `tmux attach -t orchestra-suite-<phase-slug>` or
inspect worktree `.suite/`; re-start if gone. Do not fix-and-rerun
inside this step.

```bash
orchestra suite record \
  --phase "<phase-slug>" \
  --effort "<focus>" \
  --cwd <phase-worktree>

canon create --type tuner:finding \
  --subject "suite-advisory-<phase-slug>" \
  --payload '{"claim":"advisory suite fail for <phase-slug>-suite","basis":"<exit_code and failing node ids>","invalidated_when":"suite check-run passes at phase head, or human clears","effort":"<focus>","needs":"none"}' \
  --body "## Evidence

<suite output tail>

## Consequence

Advisory only — Landing is not blocked by this suite fail.

## Follow-up

Fix opportunistically or clear the finding; do not open a required-gate fix-task storm."
```

Advisory finding only when `gate=advisory` and the suite failed.

## Reviewer

Reviewer writes no store records. Parent creates them.

1. Build the restricted brief:
   `orchestra review-brief --phase <phase-slug> --base <base> --phase-head <phase-head>`
   It refuses while the suite policy is unmet at the phase head: no
   `<phase-slug>-suite` check-run, or a failed one under
   `gate=required`. A fix task moves the head, so run the suite again
   at the new head before the reviewer starts.
   (work-item Description/Approach, acceptances, requirements/
   invariants, `git diff <base>..<phase-head>` only — no
   execution-report, check-run, assessment, or assignment text).
2. Host `reviewer` if available; else read-only/explore subagent
   with [reviewer.md](references/reviewer.md). Refuse reviewer
   store writes or tree mutation.
   Orchestra derives the verdict from the findings. A finding is blocking
   only with `blocking: true` plus `requirement`, `trigger` and
   `consequence` (and `escape` for `missing-test`); otherwise it is
   advisory. A `PASS` may list advisory findings. A `judgment` finding
   always blocks.
3. Create `tuner:check-run` (`method: review`,
   `evidence_kind: review`, `revision` = phase head; `PASS`→`pass`,
   `NEEDS_WORK`→`fail`) and one `tuner:finding` per finding.
   Set `needs` by the finding type: an advisory finding gets `needs: none` and an `advisory` claim prefix,
   creates no fix task, and does not block the phase gate; a blocking
   finding gets `needs: none` when a fix task is created; `needs: human`
   for `severity: judgment` or no fix.

```bash
canon create --type tuner:check-run \
  --subject "<phase-slug>-review" \
  --payload '{"criterion_id":"<phase-slug>-review","revision":"<phase-head-sha>","result":"<pass|fail>","effort":"<focus>","method":"review","signed_by":"","evidence_kind":"review"}' \
  --body "<reviewer output, verbatim>"

canon create --type tuner:finding \
  --subject "review-<task-or-phase>-<kind>" \
  --payload '{"claim":"<kind> on <task>: <expected>","basis":"<observed>","invalidated_when":"fix lands and reviewer re-run passes, or human clears","effort":"<focus>","needs":"<none|human>"}' \
  --body "## Evidence

<expected vs observed from the finding>

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Create a fix work-item under the retry budget, or answer Needs you."
```

4. Fixable blocking findings (`spec-gap`, `behavior-bug`, `missing-test`,
   `invariant-violation`, except `severity: judgment`) → fix
   work-items via [retry-loop.md](references/retry-loop.md) and
   `retry_max_fix_tasks`. Never reopen `done`. After fixes verify,
   re-run the reviewer **once** on the new diff. Budget exhausted →
   Needs-you path; stop.
5. One `conductor:integration-report` from the reviewer's `integration`
   map. Skip when incidental or no multi-task implementation wave.
   `pass` only when verdict is `PASS` and those sections hold — a
   clean git merge is not enough.

```bash
canon create --type conductor:integration-report \
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

On integration-report `fail`/`blocked`, or missing passing review at
phase head: leave phase `in_progress` and stop (or fix/escalate).

## Phase gate

Run `orchestra gate <phase-slug>`. Exit 0 means the gate holds. Exit 1
lists each missing term. Exit 2 means a usage, unknown phase or config
error. Add `--cwd <phase-worktree>` to check that worktree's HEAD. Do not judge the gate from the queries below
when the command is available.

The gate holds only when all terms are true (skip review/suite terms
for incidental):

- Verification task exists and is `done`
- Every active phase acceptance: latest check-run per `criterion_id`
  passes, and a passing runner check-run at phase-head SHA
- Every latest `method=manual` check-run has `signed_by`
- Passing `method: review` / `evidence_kind: review` at phase-head
- When `suite.gate` in `orchestra.toml` is `required` (and mode ≠ `none`):
  passing `<phase-slug>-suite` at that same phase-head SHA.
  `advisory` fail does not block; `deferred` / `none` → skip
- No active `tuner:finding` for the effort has `needs` `human`

Fallback for reading the records by hand:

```bash
canon list --type score:work-item \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

canon list --type score:acceptance \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

canon list --type tuner:check-run \
  --where payload.criterion_id=<acceptance-id> --order-by recorded_at

canon list --type tuner:check-run \
  --where payload.method=review --where payload.effort=<focus> \
  --order-by recorded_at

canon list --type tuner:check-run \
  --where payload.evidence_kind=integration --where payload.effort=<focus> \
  --order-by recorded_at

canon list --type tuner:finding --where payload.effort=<focus> \
  --where payload.needs=human
```

User signs an unsigned manual check:

```bash
canon correct --type tuner:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

Gate fails → leave phase `in_progress`, name what is missing, stop.
Do not waive suite policy. `deliver`/`repair` always need verification
+ passing review at head.

## Proof packet

When the gate holds, assemble a **proof packet** before phase close
or "phase done" language (skip only when no code/claim change).
Incidental / no-Landing still get a packet when code or claims
changed. Read `## Proof` on the phase for `kind` (default `claims`).
`base` = Landing base (or merge-base with main); `revision` =
phase-head. Machine = pointers only. With
`.tuner/manifest.json`, also `orchestra verify trail` and
`orchestra verify audit --base <base> --head <revision> --require-trail`
into Machine/Attention.

```bash
canon create --type conductor:proof-packet \
  --subject "<phase-slug>" \
  --payload '{"phase":"<phase-slug>","effort":"<focus>","revision":"<phase-head-sha>","base":"<base-sha>","kind":"<demo|commands|claims|audit-triage|mixed>"}' \
  --body-file "<proof-packet-body.md>"
```

Body: `## Look`, `## Machine`, `## Attention`, `## Diff`
(`git diff --stat <base>..<revision>` or `no tree change`). Print Look
and Attention in chat. Refuse "phase complete" without a packet at
this phase-head. Head moves after fixes → new packet.

## Land

Land is a separate step after verify. Land runs only when the phase has
a Landing section. Land runs only when the gate holds at the phase head
and the proof packet exists at that head. Without a Landing section,
skip this section.

When Landing is present and the phase gate holds, commit the phase
branch from the phase worktree. The phase-branch commit will include
versioned `.canon` metadata that is in the worktree. Then run
`orchestra land --phase <phase-slug>`. Land runs `orchestra gate`
first and runs the `[land]` adapter from `orchestra.toml` only when
the gate holds. Exit 0 means landed (adapter success). Exit 1 means
the adapter did not succeed; a PR may exist. Exit 2 means a usage
error, an unknown phase, or a missing store, proof packet or config.
Exit 5 means the gate failed: land prints each missing term and
pushes nothing. Pass `--cwd <phase-worktree>`; land checks that
worktree's HEAD. Merge stays human. On a non-zero exit, stop
and ask. Ask the user before you run land, unless an active
constraint authorizes it. The Landing section names branch, worktree,
base and repo only. Do not carry out integration steps from a phase
body's Landing section by hand: a merge into the default branch, a
push, a pull request, or a store commit on the default branch. No
Landing → skip the phase-branch commit. Commit
subject `type(scope): summary`; body 1–2 sentences why.

```bash
git -C <repo>/.worktrees/<phase-slug> add -A -- .
git -C <repo>/.worktrees/<phase-slug> commit -m "$(cat <<'EOF'
feat(<phase-slug>): <summary>

Commit the phase branch from the phase worktree so the work has a revision.

EOF
)"
```

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
6. Run `orchestra land --phase <phase-slug>` again. Land pushes the
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

## Close

Close is the last phase-end step. With a Landing section, close runs
after the human merges the PR. Run `orchestra close --phase
<phase-slug>` from the main checkout, not from a worktree that close
removes. Close reads the landing record and asks `gh` for the PR state.
It acts only when the PR is merged. Exit 0 means close finished, found
nothing left to do, or found the PR still open. Exit 1 means close
refused and named the path or branch: fix it, then run close again.
Exit 2 means a usage, store or `gh` error.

Close removes the task and phase worktrees, deletes the `task/*` and
`phase/*` branches, updates the effort position, closes the phase
position, and marks the phase done. It skips each step already done.
Session start runs `orchestra close --all`, so a merge between sessions
closes on its own.

Without a Landing section, close the phase by hand when the gate holds.

Close the phase; close the phase position (`subject` = phase slug,
`status: closed`) only when a note position exists; update effort
position narrative (`subject` = focus). Keep `scope` identical to the predecessor's. Set `phase`
to the next phase the narrative names — pointer only; current phase is still derived from `score:phase`
state:

```bash
canon update --type score:phase --id <phase-id> \
  --transition done --expected-revision <revision>

canon supersede --type score:position --id <phase-position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type score:position --id <effort-position-id> \
  --expected-revision <revision> \
  --payload '{"position":"<phase-slug> done; next up: <next-phase-slug>","scope":"<unchanged from predecessor>","effort":"<focus>","phase":"<next-phase-slug>"}'
```

Skip phase close commits for incidental. On revision
conflict, re-read effort position and retry. Plan the next phase only
after close. Do not materialize the next phase's tasks unless asked
(`tasks`).

If no `planned`/`in_progress` phase remains for this effort, ask
whether more phases follow. Yes → stop for `tasks`. No → close
the effort (`status: closed` on goal and position; `supersede` merges
payload so other fields carry over):

```bash
canon supersede --type score:effort --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type score:position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'
```

Reopen later: kinds-and-focus, Closing and reopening.

At `auto-phases`, plan and promote the next phase without asking. At
`gated` and `auto-plan`, ask first. At every level, stop for a failed check,
a needs-human finding, a push, or a merge.
