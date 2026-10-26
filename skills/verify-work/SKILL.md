---
name: verify-work
description: >-
  Captures aff check-run evidence, assesses what it means for
  each requirement, and closes a work-item when its requirement(s)
  are met. Use when a task needs to be shown done, a campaign was run,
  a bug was diagnosed, or a subagent returned verification evidence.
---

# Verify work

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

## Mechanical oracle verify

An acceptance is **oracle-backed** when `test_ids` and `oracle_hashes`
are both non-empty. For oracle-backed `tdd`, verification is
mechanical — not agent prose:

- Assertion-level red check-run for those frozen tests at a base
  revision (`affidavit.oracle_red.is_assertion_level_red`)
- Green check-run at head whose `revision` equals or descends from
  that red (same ancestry rules)
- At green, oracle file contents match frozen `oracle_hashes`, or a
  signed amendment in `.affidavit/manifest.json` that `aff verdict`
  accepts

Treat as verified only when those hold. Frozen hashes are close
authority — do not mark `verified` from narrative. Parent alone
writes assessments. Do not `create`/`supersede`
`aff:oracle-amendment`. Wire close-batch with green
`check_run_id`, request-carried red fields, and the acceptance id —
do not invent hash or red fields. When the claim is in
`.affidavit/manifest.json`, run `aff verdict`; non-zero → not done.

## Two modes

A phase with an active `plan:specification` is **structured**:
verify → [assess.md](references/assess.md) → `run:release`
`state` `ready` only when every requirement is verified. No
specification for this phase, and incidental work, are **simple**:
pass/fail check-runs only — no assessment or release. `kind`
`incidental` is simple even if another phase has a specification.

```bash
canon list --type plan:specification --subject "<phase-slug>" --state active
```

## Steps

1. Resolve focus, task `subject`, active `work-item` (`in_progress`),
   and its `acceptance`(s). A task may have several acceptances with
   suffixed subjects (`<task-slug>`, `<task-slug>-<suffix>`); fetch
   the family with `list --subject <task-slug>` (exact-or-prefix),
   not `get` on one id. Confirm `payload.effort` is the focus (or
   sole-goal default). If a subagent ran the check, evidence is the
   latest `run:execution-report` for that subject — read the
   record, not chat memory; trust only after you can point at a
   command, test name, diff, or metric table in its body; re-run when
   cheap. No execution-report (verified in this session without
   dispatch) → skip to step 2.
2. Capture diagnose/eval facts **before** closing:

   - `repair` — useful observations → `aff:investigation-observation`;
     known root cause → `aff:finding` with `## Evidence`,
     `## Consequence`, `## Follow-up` (all required, non-empty)
   - `evaluate` — comparative / delta / inconclusive → finding the
     same way; do not encode that in `check-run.result`

```bash
canon create --type aff:investigation-observation \
  --subject "<task-slug>" \
  --payload '{"source":"<cmd or log>","observed_time":"<iso>","environment":"<repo/rev>","what_was_observed":"<fact>","effort":"<effort-slug>"}'

canon create --type aff:finding \
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
canon update --type aff:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

   If this finding overturns a prior `plan:decision`, supersede that
   decision (see `settle-phase`) and cite the finding's subject in the
   new decision's `## Rationale`. If it contradicts an earlier
   `aff:finding`, put the earlier finding's record id in
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

     When the claim is in `.affidavit/manifest.json`, also:

```bash
aff verdict --cwd <repo-or-worktree> --at <revision> <claim-id>
```

     Exit 0 accepts; non-zero → leave `in_progress`. Do not
     `create --type aff:check-run` for `tdd`/`check`. Keep the
     runner's `id` and `result` for Assess / close.

   - `manual` — user-visible; do not mark pass without evidence the
     user would accept; plan to set `signed_by`. Create in step 4.

   Skip `check-run` only when `evaluate` is inconclusive or purely
   comparative with no binary gate — then a finding is required; do
   not transition to `done` unless the user accepts that finding.
4. For `manual` only, when a binary result exists:

```bash
canon create --type aff:check-run \
  --subject "<task-slug>" \
  --payload '{"criterion_id":"<acceptance-record-id>","revision":"<git sha or dirty>","result":"pass","effort":"<effort-slug>","method":"manual","signed_by":"","informed_by":["<acceptance-record-id>","<execution-report-id>"]}'
```

   Prefer `git rev-parse HEAD` after a commit. Leave `signed_by` `""`
   only while awaiting review (Unsigned Manual Check in handoff).
   When the user signs:

```bash
canon correct --type aff:check-run --id <check-run-id> \
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
   [assess.md](references/assess.md) before step 5.
   **Simple work:** skip Assess; use
   [close-batch.md](references/close-batch.md) for the `done` batch
   (steps 3–5), or the manual transitions below.

5. On **pass** (simple: binary gate met or evaluate finding accepted;
   structured: Assess `verified` for each requirement this work-item
   covers), orchestra moves the work-item to `done`:

```bash
canon update --type plan:work-item --id <id> \
  --transition done --expected-revision <revision>
```

   Acceptance definitions stay `active`. Closing `done` while the
   latest check-run is `fail` or missing is only legitimate as an
   explicit call — create a finding with `needs` `human` **before**
   the transition:

```bash
canon create --type aff:finding \
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
7. On **abandoned** approach: `create --type run:failed-attempt`
   with `attempted_action`, `retry_when`, `effort`. If the whole task
   is dropped, transition to `withdrawn` instead of `done`; else
   leave `in_progress`.

```bash
canon update --type plan:work-item --id <id> \
  --transition withdrawn --expected-revision <revision>
```

8. Run `canon validate`. To show state, print `orchestra view
   verification --effort <focus>`.

## Close

Simple-work `done` batch (red-first, refusal gates, request JSON):
[close-batch.md](references/close-batch.md). Structured work does not
use that batch for assessment fields — check-runs then Assess.

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

- Dual-write CI as records if CI already owns the result
- `create --type aff:check-run` for `tdd`/`check` — only
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
- Put `level` or `next` on a check-run
- Treat a failing concurrency test as proof the design is wrong
- Send every failure to `execute`; escalate by failure count; insert
  `plan`/`integration` under a repeated implementation failure
- Write `run:release` with `state` other than `ready`, or deploy
- Write assessment or release for incidental / no-specification phases
- Tell the parent to run a suite the acceptance does not name
- Edit the tree from a verification task when its check fails
- Route `manual` through `orchestra check`
- Mark oracle-backed `verified` without mechanical oracle verify
- Invent `oracle_hashes` or a signed amendment; `create`/`supersede`
  `aff:oracle-amendment`
- Treat a non-zero `aff verdict` as done
