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
`orchestra suite start` / `poll` / `collect` / `cancel` / `record` in the phase
worktree; one check-run at phase-head SHA, subject
`<phase-slug>-suite`, `evidence_kind: integration`, with runner
metadata. Dirty-only pass refused like `orchestra check`. Suite is
never red-first.

`suite start` returns an immutable `run_id`. Pass it to `poll`, `collect`,
and `record` when you inspect an older run. Add `--timeout <seconds>` to
bound a run. Cancel with `orchestra suite cancel --run-id <run_id>`.
The `--session` option remains a job label.

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

For an orphaned worker, inspect the run's `worker.log`, `result.json`, and
`output.log` under `.suite/jobs/`. Older `.suite/<label>.log` and
`.suite/<label>.exit` files are diagnostic only. Do not signal saved PIDs.
Do not fix-and-rerun inside this step.

```bash
orchestra suite record \
  --phase "<phase-slug>" \
  --effort "<focus>" \
  --cwd <phase-worktree> \
  --run-id "<run-id>"

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

Land is the `land` workflow step, separate from and after verify. Land runs only when the phase has
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
worktree's HEAD. Merge stays human. Run land without asking when
the gate holds: opening the PR is part of land. On exit 1 with the
`github-pr` adapter, follow the CI repair loop. On any other non-zero
exit, stop and ask. The Landing section names branch, worktree,
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

Merging the base branch (`main`) into the phase branch is routine.
Do it without asking when the phase branch is behind the base, or when
land or the PR reports it is out of date. Commit the merge in the phase
worktree, then run `orchestra gate` at the new head. Stop and ask only
when the merge conflicts.

Land ends when `orchestra land` exits 0. The phase is then landed and
waits for the human merge. Merge stays human. On exit 1 the adapter
reports a failure. When `[land] adapter` is `github-pr`, follow
`land-github-pr.md` for the CI repair loop. Another adapter ships its
own guide; without one, stop and ask.

## Close

Close is the last phase-end step. With a Landing section, it runs after
the human merges the phase branch. When `[land] adapter` is
`github-pr`, follow `land-github-pr.md` for the close step. Another
adapter ships its own close step; without one, close the phase by hand.

At phase close, the parent removes each task worktree `<repo>/.worktrees/<phase-slug>--<task-slug>` for that phase.

At phase close, the parent deletes each `task/<phase-slug>/<task-slug>` branch that is contained in the phase branch.

Without a Landing section, or without an adapter close step, close the
phase by hand when the gate holds.

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
