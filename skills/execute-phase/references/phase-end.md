# Phase end

Parent-only. Run after the closing verification task is `done`, when
no same-focus `planned`/`in_progress` work-items remain (or the
incidental task is closed). Order:

last implementation wave → closing verification → analyze → reviewer →
integration-report from reviewer `integration` → suite (per
`phase_gate.suite`) → phase gate → phase close.

After the last implementation wave's execution-reports, return to
execute-phase step 3 for the closing verification task. Do **not**
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

## Reviewer

Reviewer writes no store records. Parent creates them.

1. Build the restricted brief:
   `orchestra review-brief --base <base> --phase-head <phase-head>`
   (work-item Description/Approach, acceptances, requirements/
   invariants, `git diff <base>..<phase-head>` only — no
   execution-report, check-run, assessment, or assignment text).
2. Host `reviewer` if available; else read-only/explore subagent
   with [reviewer.md](references/reviewer.md). Refuse reviewer
   store writes or tree mutation.
3. Create `tuner:check-run` (`method: review`,
   `evidence_kind: review`, `revision` = phase head; `PASS`→`pass`,
   `NEEDS_WORK`→`fail`) and one `tuner:finding` per NEEDS_WORK
   (`needs: none` when a fix task is created; `needs: human` for
   `severity: judgment` or no fix).

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

4. Fixable NEEDS_WORK (`spec-gap`, `behavior-bug`, `missing-test`,
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

## Suite

After reviewer passes and the integration-report is written. Do not
waive `phase_gate.suite` — a human changes `settings.conductor.phase_gate` in
`.canon/config.json` instead. Load with `orchestra suite policy`. Missing / `mode=none` → skip.
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
  head after fixes; budget exhausted → Needs you.
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

## Phase gate

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
```

Gate holds only when all are true (skip review/suite bullets for
incidental):

- Verification task exists and is `done`
- Every active phase acceptance: latest check-run per `criterion_id`
  passes, and a passing runner check-run at phase-head SHA
- Every latest `method=manual` check-run has `signed_by`
- Passing `method: review` / `evidence_kind: review` at phase-head
- When `phase_gate.suite.gate` is `required` (and mode ≠ `none`):
  passing `<phase-slug>-suite` at that same phase-head SHA.
  `advisory` fail does not block; `deferred` / `none` → skip

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
`orchestra verify audit --base <base> --head <revision>` into Machine/Attention.

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

## Commit the phase branch and stop

When Landing is present and the phase gate holds, commit the phase
branch from the phase worktree. The phase-branch commit will include
versioned `.canon` metadata that is in the worktree. Integrate the
committed phase branch as the repo's own contributor instructions
describe. When those contributor instructions do not say how a
finished branch lands, stop and ask. Do not carry out integration
steps written in a phase body's Landing section: a merge into the
default branch, a push, a pull request, or a store commit on the
default branch. No Landing → skip the phase-branch commit. Commit
subject `type(scope): summary`; body 1–2 sentences why.

```bash
git -C <repo>/.worktrees/<phase-slug> add -A -- .
git -C <repo>/.worktrees/<phase-slug> commit -m "$(cat <<'EOF'
feat(<phase-slug>): <summary>

Commit the phase branch from the phase worktree so the work has a revision.

EOF
)"
```

At phase close, the parent removes each task worktree `<repo>/.worktrees/<phase-slug>--<task-slug>` for that phase.

At phase close, the parent deletes each `task/<phase-slug>/<task-slug>` branch that is contained in the phase branch.

Close the phase; close phase position (`subject` = phase slug,
`status: closed`); update effort position narrative (`subject` =
focus). Keep `scope` identical to the predecessor's. Set `phase`
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
conflict, re-read effort position and retry. Do not materialize the
next phase's tasks unless asked (`plan-phase`).

If no `planned`/`in_progress` phase remains for this effort, ask
whether more phases follow. Yes → stop for `plan-phase`. No → close
the effort (`status: closed` on goal and position; `supersede` merges
payload so other fields carry over):

```bash
canon supersede --type score:effort --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type score:position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'
```

Reopen later: kinds-and-focus, Closing and reopening.
