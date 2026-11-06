# verify-work mechanics

Full step-by-step mechanics. SKILL.md keeps the judgment; this file is the manual fallback and the record of every contract.

## Verify work

Requires `canon` and `orchestra` on PATH and a live
orchestra store. If missing,
follow [ensure-store.md](references/ensure-store.md). Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Parent session
writes records. Git/tests own the code; this skill owns the
occurrence that a requirement was checked (via acceptance
`verify_command`) and any diagnose/eval conclusion. Claim text is
requirement id + original wording (specification `## Requirements`,
or work-item Description) — not acceptance `criterion` prose.

`method`: `tdd` | `check` | `manual`. Work-item `kind`: `deliver` |
`repair` | `evaluate` | `incidental`. Task state is lifecycle
`in_progress -> done` or `withdrawn` — no `live` field.

**Red-first** for `tdd` on a `done` close is enforced by
`orchestra close-batch`: pass-only `tdd` without request-carried red
is refused (exit 2), same as unmet criteria without a finding. The
close-request must name a runner-produced fail via `red_check_run_id`
and copy that fail's fields (script does not query prior check-runs).
Green revision must equal or descend from red, or red may be `dirty`
with non-empty `red_diff_sha256`. Closing `tdd` pass without red
needs the same finding escape as unmet criteria. `check` and
`manual` do not require red.

Verify asks what happened. Assess asks what that means and what is
next. A check-run has no `level` and no `next`.

Verified status is derived, not written: `orchestra view verification`
reports a requirement `verified` when its acceptances have passing
check-runs. Write a `conductor:assessment` only for a non-verified
status (`failed`, `insufficient`, `blocked`). A written non-verified
assessment wins over derivation until every acceptance for the
requirement has a passing check-run recorded after it.

Write the records for one task through one `canon apply` call (step
8). The `canon create`, `update`, and `supersede` commands in this
skill show the payload of each batch line; do not run them one by one.

## Mechanical oracle verify

Select method separately from [oracle policy](../../plan-phase/references/verification-policy.md).
Legacy non-empty `test_ids` and `oracle_hashes` remain **oracle-backed**.
For frozen `check`, enforce green hashes without red. For frozen `tdd`, verification is
mechanical — not agent prose:

- Assertion-level red check-run for those frozen tests at a base
  revision (`orchestra verify assertion-red <check-run.json>`)
- Green check-run at head whose `revision` equals or descends from
  that red (same ancestry rules)
- At green, oracle file contents match frozen `oracle_hashes`, or a
  signed amendment in `.tuner/manifest.json` that `orchestra verify verdict`
  accepts

Treat as verified only when those hold. Frozen hashes are close
authority — do not treat a requirement as `verified` from narrative.
When they do not hold, write an `insufficient` assessment so the
derived `verified` does not stand. Parent alone writes assessments. Do not `create`/`supersede`
`tuner:oracle-amendment`. Wire close-batch with green
`check_run_id`, request-carried red fields, and the acceptance id —
do not invent hash or red fields. When the claim is in
`.tuner/manifest.json`, run `orchestra verify verdict`; non-zero → not done.

## Two modes

A phase with an active `score:specification` is **structured**:
verify → [assess.md](references/assess.md), which writes an assessment
only for a non-verified status. Release `ready` is derived when
every requirement is verified; write no `conductor:release`. No
specification for this phase, and incidental work, are **simple**:
pass/fail check-runs only — no assessment or release. `kind`
`incidental` is simple even if another phase has a specification.

```bash
canon list --type score:specification --subject "<phase-slug>" --state active
```

## Steps

1. Resolve focus, task `subject`, active `work-item` (`in_progress`),
   and its `acceptance`(s). A task may have several acceptances with
   suffixed subjects (`<task-slug>`, `<task-slug>-<suffix>`); fetch
   the family with `list --subject <task-slug>` (exact-or-prefix),
   not `get` on one id. Confirm `payload.effort` is the focus (or
   sole-goal default). If a subagent ran the check, evidence is the
   latest `conductor:execution-report` for that subject — read the
   record, not chat memory; trust only after you can point at a
   command, test name, diff, or metric table in its body; re-run when
   cheap. No execution-report (verified in this session without
   dispatch) → skip to step 2.
2. Capture diagnose/eval facts **before** closing. Each is a line of
   the step-8 batch, ordered before the work-item transition:

   - `repair` — useful observations → `tuner:investigation-observation`;
     known root cause → `tuner:finding` with `## Evidence`,
     `## Consequence`, `## Follow-up` (all required, non-empty)
   - `evaluate` — comparative / delta / inconclusive → finding the
     same way; do not encode that in `check-run.result`

```bash
canon create --type tuner:investigation-observation \
  --subject "<task-slug>" \
  --payload '{"source":"<cmd or log>","observed_time":"<iso>","environment":"<repo/rev>","what_was_observed":"<fact>","effort":"<effort-slug>"}'

canon create --type tuner:finding \
  --subject "<task-slug>" \
  --payload '{"claim":"<cause or comparison>","basis":"<evidence>","invalidated_when":"<what would undo this>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<what was run/observed and its output>

## Consequence

<what this means for the task/decision it bears on>

## Follow-up

<what someone should do next, or \"none\">"
```

   `needs` is `human` when a maintainer call is required before close
   (surfaces in handoff Needs Human), else `none`. Clear at the event
   when the user decides (kinds-and-focus, Needs-you clears):

```bash
canon update --type tuner:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

   If this finding overturns a prior `score:decision`, supersede that
   decision (see `settle-phase`) and cite the finding's subject in the
   new decision's `## Rationale`. If it contradicts an earlier
   `tuner:finding`, put the earlier finding's record id in
   `contradicted_by` (a JSON array) in the new finding's payload.

## Verify

For `tdd`/`check`, the runner writes the check-run — do not `create`
those by hand. For `manual`, create it yourself. Do not put `level`
or `next` on a check-run.

3. Run the binary criterion when `method` is `tdd` / `check` / a
   `manual` pass/fail, or when `evaluate` has a binary gate:

   - `tdd` / `check` — `orchestra check` runs
     `acceptance.verify_command`, maps outcome to `result`, creates
     the check-run. A first failing TDD run is expected — do not
     record a `failed-attempt` for that first red. Pass
     `--execution-report` when step 1 has one; `--cwd` for a phase
     worktree; `--allow-dirty` only for an explicit dirty pass.

```bash
orchestra check --acceptance <acceptance-record-id> \
  --cwd <repo-or-worktree> \
  --execution-report <execution-report-record-id>
```

     When the claim is in `.tuner/manifest.json`, also:

```bash
orchestra verify verdict --cwd <repo-or-worktree> --at <revision> <claim-id>
```

     Exit 0 accepts; non-zero → leave `in_progress`. Do not
     `create --type tuner:check-run` for `tdd`/`check`. Keep the
     runner's `id` and `result` for Assess / close.

   - `manual` — user-visible; do not mark pass without evidence the
     user would accept; plan to set `signed_by`. Create in step 4.

   Skip `check-run` only when `evaluate` is inconclusive or purely
   comparative with no binary gate — then a finding is required; do
   not transition to `done` unless the user accepts that finding.
4. For `manual` only, when a binary result exists (a line of the
   step-8 batch):

```bash
canon create --type tuner:check-run \
  --subject "<task-slug>" \
  --payload '{"criterion_id":"<acceptance-record-id>","revision":"<git sha or dirty>","result":"pass","effort":"<effort-slug>","method":"manual","signed_by":"","informed_by":["<acceptance-record-id>","<execution-report-id>"]}'
```

   Prefer `git rev-parse HEAD` after a commit. Leave `signed_by` `""`
   only while awaiting review (Unsigned Manual Check in handoff).
   When the user signs:

```bash
canon correct --type tuner:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

   `tdd`/`check` keep `signed_by` `""`. `result` is `pass` | `fail` |
   `blocked` | `insufficient`. `pass` covers only the linked
   requirement and that `evidence_kind`. `fail` means the check ran
   and the requirement was not met — not that the design is wrong.
   When the acceptance has `requirement`, put that id and an
   `evidence_kind` from the schema enum on the check-run (runner or
   manual create). Still no `level`/`next`.

   **Structured work:** after check-runs, follow
   [assess.md](references/assess.md) before step 5. Assess adds batch
   lines for non-verified requirements only.
   **Simple work:** skip Assess; use
   [close-batch.md](references/close-batch.md) for the `done` batch
   (steps 3–5), or the manual transitions below.

5. On **pass** (simple: binary gate met or evaluate finding accepted;
   structured: no written non-verified assessment and every
   requirement this work-item covers derives `verified`), orchestra
   moves the work-item to `done` (the last line of the step-8 batch):

```bash
canon update --type score:work-item --id <id> \
  --transition done --expected-revision <revision>
```

   Acceptance definitions stay `active`. Closing `done` while the
   latest check-run is `fail` or missing is only legitimate as an
   explicit call — create a finding with `needs` `human` **before**
   the transition:

```bash
canon create --type tuner:finding \
  --subject "<task-slug>" \
  --payload '{"claim":"<task-slug> closed done with an unmet or unverified criterion","basis":"<why it was closed anyway>","invalidated_when":"<what would undo this acceptance>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<the failing/missing check-run and why closing proceeded anyway>

## Consequence

<what remains unverified>

## Follow-up

<what someone should do to close the gap, or \"none\">"
```

6. On **fail** for simple work (not the intentional TDD red you will
   fix next): leave `in_progress`. Optionally open a blocking
   `continuity-question` on the focus if dispatch must stop.
   Structured: `fail` is evidence for Assess; Assess chooses `next`.
   Do not send every failure to execute. Verification check fail
   caused by the task's code → leave `in_progress`, assessment
   `next` `execute`; do not tell the parent to run a suite the
   acceptance does not name. Parent (`execute-phase`) re-dispatches
   or creates fix tasks — this skill does not.
7. On **abandoned** approach: `create --type conductor:failed-attempt`
   with `attempted_action`, `retry_when`, `effort`. If the whole task
   is dropped, transition to `withdrawn` instead of `done`; else
   leave `in_progress`.

```bash
canon update --type score:work-item --id <id> \
  --transition withdrawn --expected-revision <revision>
```

8. Write the batch. Collect every record from steps 2 to 7 for this
   task into one NDJSON file and run `canon apply` once. Runner
   check-runs from `orchestra check` already exist; do not repeat
   them. Each line is `{"op": ..., "type": ..., ...}`: `create` takes
   `subject`, `payload`, `body`; `update` takes `id`, `transition` or
   `payload`, `expected_revision`; `supersede` takes `id`, `payload`,
   `body`, `expected_revision`. Use `"expected_revision": "@current"`
   when the record was read earlier in this session. Put the
   work-item transition on the last line. Example for a repair task
   that passes with a finding and a manual check-run:

```bash
cat > /tmp/verify-batch.ndjson <<'EOF'
{"op":"create","type":"tuner:finding","subject":"<task-slug>","payload":{"claim":"<cause>","basis":"<evidence>","invalidated_when":"<what would undo this>","effort":"<effort-slug>","needs":"none"},"body":"## Evidence\n\n<output>\n\n## Consequence\n\n<meaning>\n\n## Follow-up\n\nnone"}
{"op":"create","type":"tuner:check-run","subject":"<task-slug>","payload":{"criterion_id":"<acceptance-record-id>","revision":"<git sha>","result":"pass","effort":"<effort-slug>","method":"manual","signed_by":"","informed_by":["<acceptance-record-id>","<execution-report-id>"]}}
{"op":"update","type":"score:work-item","id":"<work-item-id>","transition":"done","expected_revision":"@current"}
EOF
canon apply /tmp/verify-batch.ndjson
```

   `canon apply` prints `{"ok", "applied", "failed", "results"}`. It
   does not stop at a failed line: later lines still run. On
   `"ok": false`, print each failed entry of `results` and the
   input line with the same `line` number, then fix that line and
   apply a file with the failed lines only. Never re-apply lines that
   succeeded. If a finding, assessment, or check-run line failed
   while the transition line applied, fix and apply the failed line
   at once.
9. Run `canon validate`. To show state, print `orchestra view
   verification --effort <focus>`.

## Close

Simple-work `done` batch (red-first, refusal gates, request JSON):
[close-batch.md](references/close-batch.md). Structured work does not
use that batch for assessment fields — check-runs then Assess.

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

- Dual-write CI as records if CI already owns the result
- `create --type tuner:check-run` for `tdd`/`check` — only
  `orchestra check` (or an already runner-produced id)
- Invent pass/fail in a close-request for `tdd`/`check` without a
  runner `check_run_id`
- Treat a checklist tick as pass without a `check-run` or `finding`
- Transition to `done` on unmet/unverified criterion without the
  step-5 finding
- Put a metric table in `check-run.result`
- Leave `manual` `signed_by` empty after someone reviewed it
- Invent `red_*` fields or close pass-only `tdd` without a runner
  fail (or finding escape)
- Close another focus's work-item
- Skip `orchestra close-batch` and hand-assemble apply NDJSON for a
  multi-criterion close
- Run `canon create`, `update`, or `supersede` one by one for the
  records of one task; write them through one `canon apply`
- Write a `conductor:assessment` for a `verified` status; verified is
  derived
- Put `level` or `next` on a check-run
- Treat a failing concurrency test as proof the design is wrong
- Send every failure to `execute`; escalate by failure count; insert
  `plan`/`integration` under a repeated implementation failure
- Write `conductor:release`; release `ready` is derived. Never deploy
- Write assessment or release for incidental / no-specification phases
- Tell the parent to run a suite the acceptance does not name
- Edit the tree from a verification task when its check fails
- Route `manual` through `orchestra check`
- Let oracle-backed `verified` stand without mechanical oracle verify
- Invent `oracle_hashes` or a signed amendment; `create`/`supersede`
  `tuner:oracle-amendment`
- Treat a non-zero `orchestra verify verdict` as done
