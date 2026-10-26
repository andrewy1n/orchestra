# Phase end

Parent-only. Run after the closing verification task is `done`, when
no same-focus `planned`/`in_progress` work-items remain (or the
incidental task is closed). Order:

last implementation wave → closing verification → reviewer →
integration-report from reviewer `integration` → suite (per
`phase_gate.suite`) → phase gate → Landing merge.

After the last implementation wave's execution-reports, return to
execute-phase step 3 for the closing verification task. Do **not**
write an integration-report before verification.

Skip reviewer / review check-run / integration-report / suite when
incidental. An empty task list is not proof the phase is done — check
the gate below before closing.

## Reviewer

Reviewer writes no store records. Parent creates them.

1. Build the restricted brief:
   `orchestra review-brief --base <base> --phase-head <phase-head>`
   (work-item Description/Approach, acceptances, requirements/
   invariants, `git diff <base>..<phase-head>` only — no
   execution-report, check-run, assessment, or assignment text).
2. Host `se-reviewer` if available; else read-only/explore subagent
   with [se-reviewer.md](references/se-reviewer.md). Refuse reviewer
   store writes or tree mutation.
3. Create `aff:check-run` (`method: review`,
   `evidence_kind: review`, `revision` = phase head; `PASS`→`pass`,
   `NEEDS_WORK`→`fail`) and one `aff:finding` per NEEDS_WORK
   (`needs: none` when a fix task is created; `needs: human` for
   `severity: judgment` or no fix).

```bash
canon create --type aff:check-run \
  --subject "<phase-slug>-review" \
  --payload '{"criterion_id":"<phase-slug>-review","revision":"<phase-head-sha>","result":"<pass|fail>","effort":"<focus>","method":"review","signed_by":"","evidence_kind":"review"}' \
  --body "<reviewer output, verbatim>"

canon create --type aff:finding \
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
5. One `run:integration-report` from the reviewer's `integration`
   map. Skip when incidental or no multi-task implementation wave.
   `pass` only when verdict is `PASS` and those sections hold — a
   clean git merge is not enough.

```bash
canon create --type run:integration-report \
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
waive `phase_gate.suite` — a human changes `settings.run.phase_gate` in
`.artifacts/config.json` instead. Load with `orchestra suite policy`. Missing / `mode=none` → skip.
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

Orphaned tmux: `tmux attach -t orchestra-suite-<phase-slug>` or
inspect worktree `.suite/`; re-start if gone. Do not fix-and-rerun
inside this step.

```bash
orchestra suite record \
  --phase "<phase-slug>" \
  --effort "<focus>" \
  --cwd <phase-worktree>

canon create --type aff:finding \
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
canon list --type plan:work-item \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

canon list --type plan:acceptance \
  --where payload.effort=<focus> --where payload.phase=<phase-slug>

canon list --type aff:check-run \
  --where payload.criterion_id=<acceptance-id> --order-by recorded_at

canon list --type aff:check-run \
  --where payload.method=review --where payload.effort=<focus> \
  --order-by recorded_at

canon list --type aff:check-run \
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
canon correct --type aff:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

Gate fails → leave phase `in_progress`, name what is missing, stop.
Do not waive suite policy. `deliver`/`repair` always need verification
+ passing review at head.

## Proof packet

When the gate holds, assemble a **proof packet** before Landing merge
or "phase done" language (skip only when no code/claim change).
Incidental / no-Landing still get a packet when code or claims
changed. Read `## Proof` on the phase for `kind` (default `claims`).
`base` = Landing base (or merge-base with main); `revision` =
phase-head. Machine = pointers only. With
`.affidavit/manifest.json`, also `aff trail` and
`aff audit --base <base> --head <revision>` into Machine/Attention.

```bash
canon create --type run:proof-packet \
  --subject "<phase-slug>" \
  --payload '{"phase":"<phase-slug>","effort":"<focus>","revision":"<phase-head-sha>","base":"<base-sha>","kind":"<demo|commands|claims|audit-triage|mixed>"}' \
  --body-file "<proof-packet-body.md>"
```

Body: `## Look`, `## Machine`, `## Attention`, `## Diff`
(`git diff --stat <base>..<revision>` or `no tree change`). Print Look
and Attention in chat. Refuse "phase complete" without a packet at
this phase-head. Head moves after fixes → new packet.

## Landing merge and close

With Landing: commit phase branch from worktree (exclude
`.artifacts`); from primary checkout merge into `main`; store commit
on `main` follows phase close. Push only when Landing names push as a
human stop — otherwise do not push. No Landing → skip branch commit,
merge, and store commit. Commit subject `type(scope): summary`; body
1–2 sentences why.

```bash
git -C <repo>/.worktrees/<phase-slug> add -A -- . ':!.artifacts'
git -C <repo>/.worktrees/<phase-slug> commit -m "$(cat <<'EOF'
feat(<phase-slug>): <summary>

Commit the phase branch so the merge onto main has a revision to land.

EOF
)"
git -C <primary-checkout> merge phase/<phase-slug>
```

At phase close, the parent removes each task worktree `<repo>/.worktrees/<phase-slug>--<task-slug>` for that phase.

At phase close, the parent deletes each `task/<phase-slug>/<task-slug>` branch that is contained in the phase branch.

Close the phase; close phase position (`subject` = phase slug,
`status: closed`); update effort position narrative (`subject` =
focus). Keep `scope` identical to the predecessor's. Set `phase`
to the next phase the narrative names — pointer only; current phase is still derived from `plan:phase`
state:

```bash
canon update --type plan:phase --id <phase-id> \
  --transition done --expected-revision <revision>

canon supersede --type plan:position --id <phase-position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type plan:position --id <effort-position-id> \
  --expected-revision <revision> \
  --payload '{"position":"<phase-slug> done; next up: <next-phase-slug>","scope":"<unchanged from predecessor>","effort":"<focus>","phase":"<next-phase-slug>"}'
```

Then store commit on `main` (Landing only):

```bash
git -C <primary-checkout> add -- .artifacts
git -C <primary-checkout> commit -m "$(cat <<'EOF'
chore(<phase-slug>): record the store

Commit the store on main so the record diff shows what changed and why.

EOF
)"
```

Skip phase close / Landing commits for incidental. On revision
conflict, re-read effort position and retry. Do not materialize the
next phase's tasks unless asked (`plan-phase`).

If no `planned`/`in_progress` phase remains for this effort, ask
whether more phases follow. Yes → stop for `plan-phase`. No → close
the effort (`status: closed` on goal and position; `supersede` merges
payload so other fields carry over):

```bash
canon supersede --type plan:effort --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'

canon supersede --type plan:position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"closed"}'
```

Reopen later: kinds-and-focus, Closing and reopening.
