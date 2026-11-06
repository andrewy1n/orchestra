---
name: verify-work
description: >-
  Captures check-run evidence, assesses what it means for
  each requirement, and closes a work-item when its requirement(s)
  are met. Use when a task needs to be shown done, a campaign was run,
  a bug was diagnosed, or a subagent returned verification evidence.
---

# Verify work

Requires `canon` and `orchestra` on PATH and a live orchestra store.
If missing, follow [ensure-store.md](references/ensure-store.md).
Follow [kinds-and-focus.md](references/kinds-and-focus.md). Parent
session writes records. Git/tests own the code; this skill owns the
occurrence that a requirement was checked (via acceptance
`verify_command`) and any diagnose/eval conclusion. Claim text is
requirement id + original wording, not acceptance `criterion` prose.
Record shapes: [mechanics.md](references/mechanics.md).

**Red-first** for `tdd` on a `done` close is enforced by
`orchestra close-batch`: pass-only `tdd` without request-carried red
is refused (exit 2). The close-request names a runner-produced fail
via `red_check_run_id` and copies that fail's fields. Green revision
equals or descends from red, or red is `dirty` with non-empty
`red_diff_sha256`. `check` and `manual` do not require red.

Verify asks what happened. Assess asks what that means and what is
next. A check-run has no `level` and no `next`. Verified status is
derived: `orchestra view verification` reports a requirement
`verified` when its acceptances have passing check-runs. Write a
`conductor:assessment` only for a non-verified status (`failed`,
`insufficient`, `blocked`). It wins over derivation until every
acceptance for the requirement has a later passing check-run.

## Mechanical oracle verify

Select method separately from [oracle policy](../plan-phase/references/verification-policy.md).
Legacy non-empty `test_ids` and `oracle_hashes` remain **oracle-backed**.
For frozen `check`, enforce green hashes without red. For frozen `tdd`, verification is
mechanical, not agent prose. Treat as verified only when all hold:

- Assertion-level red check-run for the frozen tests at a base
  revision (`orchestra verify assertion-red <check-run.json>`)
- Green check-run at head whose `revision` descends from red
- At green, oracle file contents match frozen `oracle_hashes`, or a
  signed amendment in `.tuner/manifest.json` that `orchestra verify verdict`
  accepts

Frozen hashes are close authority: never mark `verified` from
narrative; otherwise write an `insufficient` assessment (parent only).
Wire close-batch with green `check_run_id`, red fields, and the
acceptance id.

## Two modes
A phase with an active `score:specification` is **structured**:
verify -> [assess.md](references/assess.md). Release `ready` is
derived; write no `conductor:release`. No specification, and
incidental work, are **simple**: pass/fail check-runs only.

## Steps

1. Resolve focus, task `subject`, active `work-item` (`in_progress`),
   and its `acceptance`(s) (`list --subject <task-slug>`). If a subagent ran the check,
   evidence is the latest `conductor:execution-report` for that
   subject (`orchestra task land` writes it and runs the checks). Read
   the record, not chat memory. Trust it only after you can point at a
   command, test name, diff, or metric table in its body.
2. Capture diagnose/eval facts **before** closing, as batch lines
   ordered before the work-item transition. `repair`: observations ->
   `tuner:investigation-observation`; known root cause ->
   `tuner:finding` with `## Evidence`, `## Consequence`,
   `## Follow-up` (all non-empty). `evaluate`: comparative / delta /
   inconclusive -> finding, not `check-run.result`. `needs` is `human`
   when a maintainer call is required before close, else `none`. A
   finding that overturns a `score:decision` supersedes it (see
   `settle-phase`); one that contradicts an earlier finding cites it
   in `contradicted_by`.

## Verify
3. For `tdd`/`check`, the runner writes the check-run. Do not `create`
   those by hand. `orchestra check --acceptance <id> --cwd <dir>
   [--execution-report <id>]` runs `acceptance.verify_command`. A first
   failing TDD run is expected; record no `failed-attempt` for it.
   When the claim is in
   `.tuner/manifest.json`, also run `orchestra verify verdict --cwd
   <dir> --at <revision> <claim-id>`; non-zero -> leave `in_progress`.
   Skip the check-run only when `evaluate` is inconclusive; then a
   finding is required and `done` needs the user's acceptance of it.
4. For `manual` only, add a `tuner:check-run` line with `method`
   `manual` and `signed_by` `""` until the user signs (then `canon
   correct`). Do not mark pass without evidence the user would accept.
   `result` is `pass` | `fail` | `blocked` | `insufficient`. `pass`
   covers only the linked requirement and its `evidence_kind`.
   Structured work: follow [assess.md](references/assess.md) before
   step 5. Simple work: use [close-batch.md](references/close-batch.md).
5. On **pass**, move the work-item to `done` (last batch line): simple
   work when the binary gate is met or the finding is accepted;
   structured work when no non-verified assessment stands and every
   requirement derives `verified`. Closing `done` on a `fail` or
   missing check-run needs a finding with `needs` `human` **before**
   the transition.
6. On **fail** (not the intentional TDD red): leave `in_progress`;
   Assess chooses `next`. The parent (`execute-phase`) re-dispatches
   or creates fix tasks.
7. On **abandoned** approach: `create --type conductor:failed-attempt`
   (`attempted_action`, `retry_when`, `effort`); drop the task with
   `withdrawn` instead of `done`.
8. Write the batch: every record from steps 2 to 7 in one NDJSON file,
   through one `canon apply` call (shape in
   [mechanics.md](references/mechanics.md)). Put the work-item
   transition on the last line. On `"ok": false`, print each failed
   entry of `results`, fix, and apply only the failed lines.
9. Run `canon validate`.

## Close

Simple-work `done` batch: [close-batch.md](references/close-batch.md).

## Record versus bind

An unbound evidence-observation does not earn a manifest claim. Path:
claim id -> evidence-binding -> evidence-observation. `orchestra verify
bind` writes the evidence-binding; then `orchestra verify recheck`
before treating the claim as earned. Inspect with `orchestra verify
trail`. Command forms: [mechanics.md](references/mechanics.md).

## Do not

- `create --type tuner:check-run` for `tdd`/`check`; only
  `orchestra check` writes them. Invent pass/fail, `red_*` fields, or
  a close-request without a runner `check_run_id`
- Treat a checklist tick as pass; close `done` on an unmet criterion
  without the step-5 finding
- Put a metric table in `check-run.result`, or `level`/`next` on one;
  leave `manual` `signed_by` empty after review; route `manual`
  through `orchestra check`
- Close another focus's work-item; dual-write CI results as records;
  run `canon create`, `update`, or `supersede` one by one for one
  task (use one `canon apply`)
- Write a `conductor:assessment` for a `verified` status, a
  `conductor:release`, or either for simple work. Never deploy
- Treat a failing concurrency test as proof the design is wrong; send
  every failure to `execute`; escalate by failure count; edit the tree
  from a verification task; tell the parent to run a suite the
  acceptance does not name
- Let oracle-backed `verified` stand without mechanical oracle verify;
  invent `oracle_hashes` or a signed amendment; `create`/`supersede`
  `tuner:oracle-amendment`; treat non-zero `verify verdict` as done
