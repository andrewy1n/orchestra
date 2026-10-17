---
name: verify-work
description: >-
  Captures aff check-run evidence, assesses what it means for
  each requirement, and closes a work-item when its requirement(s)
  are met. Use when a task needs to be shown done, a campaign was run,
  a bug was diagnosed, or a subagent returned verification evidence.
---

# Verify work

Requires `artifact-runtime` and a live affidavit store. If missing,
follow [ensure-store.md](../ensure-store.md). Follow
[kinds-and-focus.md](../kinds-and-focus.md). Parent session writes
records. Git/tests own the code; this skill owns the occurrence that
a requirement was checked (via its acceptance's `verify_command`)
and any diagnose/eval conclusion. The claim text is the requirement
id plus its original wording (specification `## Requirements`, or the
work-item Description when there is no spec) — not acceptance
`criterion` prose (which may be empty on thin acceptances).

`method` on `project:acceptance`/`project:check-run`: `tdd` | `check`
| `manual`. `kind` on the work-item: `deliver` | `repair` | `evaluate`
| `incidental`. Task state is the work-item's **lifecycle** —
`in_progress -> done` or `withdrawn` — not a payload flag; there is no
`live` field.

Red-first (fail before you fix) for `method` `tdd` on a `done` close
is **enforced** by `aff close-batch`. A pass-only `tdd` close-request
without request-carried red evidence is refused (exit 2), the same
way unmet criteria without a finding are refused. The gate is
request-carried: the close-request must name a runner-produced fail
via `red_check_run_id` and copy that fail's fields; the script does
not query the store for prior check-runs. Ordering is git ancestry —
the green revision must equal or be a descendant of the red revision
— or the red may be `dirty` with a non-empty `red_diff_sha256`.
Closing a `tdd` pass without red requires the same finding escape as
closing on an unmet criterion. `check` and `manual` do not require
red evidence.

## Mechanical oracle verify

An acceptance is **oracle-backed** when `test_ids` and `oracle_hashes`
are both non-empty. For oracle-backed `tdd`, verification is
**mechanical** — not agent prose:

- There is an **assertion-level** red check-run for that acceptance's
  frozen tests at a base revision (fail with assertion-level failing
  nodes; see `affidavit.oracle_red.is_assertion_level_red`).
- There is a green check-run at head whose `revision` equals or is a
  git descendant of that red (same red-first ancestry rules).
- At the green revision, oracle file contents match frozen
  `oracle_hashes`, **or** an active `project:oracle-amendment` for
  that acceptance has `status` `approved` and `new_hashes` matching
  the tree.

Treat the requirement as verified only when those hold. Frozen
hashes are close authority; do not mark `verified` from narrative
alone. Parent alone writes assessments and freeze / amendment
records. Wire the close-request (below) so `aff close-batch` receives
the green `check_run_id`, request-carried red fields, and the
acceptance id whose freeze / amendment state close-batch enforces —
do not invent hash or red fields.

Verify and assess are two steps. Verify asks what happened. Assess
asks what that evidence means and what happens next. A check-run has
no `level` and no `next`.

## Two modes

Decision two-modes. A phase with a `project:specification` is
structured work: verify, assess, then `project:release` with `state`
`ready` only when every requirement is verified. A phase with no
specification, and incidental work, skip assessment and release and
keep pass/fail check-runs. `kind` `incidental` is incidental work even
when a specification exists for some other phase.

```bash
adaptive-artifacts list --type project:specification --subject "<phase-slug>" --state active
```

No active specification for this phase means simple work. Do not write
`project:assessment` or `project:release` on that path.

## Steps

1. Resolve focus, the task `subject`, its active `work-item`
   (`in_progress`), and its `acceptance`(s). A task can have several
   acceptances sharing a suffixed subject (`<task-slug>`,
   `<task-slug>-<suffix>` — the `plan-phase` convention); fetch the
   whole family with `list --subject <task-slug>` (exact-or-prefix
   match), not `get` on a single id. Confirm `payload.effort` is the
   focus (or the sole-goal default). If a subagent ran the check, its
   evidence is the `project:execution-report` `execute-phase` created
   for that dispatch — read that record (`list --type
   project:execution-report --subject <task-slug>`, take the most
   recent), not this session's memory of the chat — and trust it only
   after you can point at a command, test name, diff, or metric table
   inside its body; re-run when cheap. There is no execution-report
   when this task was verified without a dispatch (e.g. done directly
   in this session) — skip straight to step 2 in that case.
2. Capture diagnose/eval facts **before** closing anything:

   - `repair` — for each useful observation, `create --type
     project:investigation-observation` with the task `subject` and
     `effort`. When a root cause is known, `create --type
     project:finding` with `--body-file`/`--body` carrying
     `## Evidence`, `## Consequence`, `## Follow-up` (all required,
     all non-empty).
   - `evaluate` — if the result is comparative, a delta, or
     inconclusive, `create --type project:finding` the same way. Do
     not encode that in `check-run.result`.

```bash
adaptive-artifacts create --type project:investigation-observation \
  --subject "<task-slug>" \
  --payload '{"source":"<cmd or log>","observed_time":"<iso>","environment":"<repo/rev>","what_was_observed":"<fact>","effort":"<effort-slug>"}'

adaptive-artifacts create --type project:finding \
  --subject "<task-slug>" \
  --payload '{"claim":"<cause or comparison>","basis":"<evidence>","invalidated_when":"<what would undo this>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<what was run/observed and its output>

## Consequence

<what this means for the task/decision it bears on>

## Follow-up

<what someone should do next, or \"none\">"
```

   `needs` is `human` when this finding needs a maintainer call before
   the task can close (it then surfaces in `handoff`'s Needs Human
   section), else `none`. When the user decides a `needs` `human`
   finding, clear it at the event (kinds-and-focus, Needs-you clears):

```bash
adaptive-artifacts update --type project:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

   If this finding overturns a prior
   `project:decision`, add `--rel contradicts:<decision-record-id>` to
   the `create` call above — `contradict` (the subcommand) only works
   on record types with `contradiction: separate_record`, which is
   `project:finding` itself, not the decision it's contradicting; a
   plain `create --rel contradicts:...` is the correct shape for
   finding-contradicts-decision.

## Verify

Verify asks what happened. For `tdd`/`check`, the runner writes the
check-run — do not `create` those by hand. For `manual`, create the
check-run yourself. Assessments (what evidence means) stay in this
skill. Do not write `level` or `next` on a check-run.

3. Run the binary criterion when `method` is `tdd` / `check` / a
   `manual` pass/fail, or when `evaluate` has a binary gate:

   - `tdd` / `check` — invoke the plugin CLI. It runs
     `acceptance.verify_command`, maps the process outcome to
     `result`, and creates the `project:check-run` (with runner
     fields, `revision`, and `informed_by` the acceptance). A first
     failing TDD run is expected; do not record a `failed-attempt`
     for that first red. Pass `--execution-report` when step 1 has
     one for this dispatch. Pass `--cwd` when the code lives in a
     phase worktree. Use `--allow-dirty` only for an explicit dirty
     pass (fails may be dirty without it).

```bash
aff check --acceptance <acceptance-record-id> \
  --cwd <repo-or-worktree> \
  --execution-report <execution-report-record-id>
```

     Resolve `affidavit` from the plugin root (`bin/aff`)
     the same way [ensure-store.md](../ensure-store.md) resolves
     `<plugin>`. Do **not** `adaptive-artifacts create --type
     project:check-run` for `method` `tdd` or `check`. Read the
     runner's JSON (or `list` the new check-run) and keep its `id`
     and `result` for Assess and for `close`.

   - `manual` — user-visible check; do not mark pass without evidence
     the user would accept, and plan to set `signed_by` once they do.
     Create the check-run yourself (step 4).

   Skip `check-run` only when `evaluate` is inconclusive or purely
   comparative with no binary gate. A finding is then required; do
   **not** transition the work-item to `done` unless the user accepts
   that finding as done.
4. For `manual` only, when a binary result exists, `create --type
   project:check-run` with the same `subject`. Add a second `--rel
   informed_by:` pointing at the execution-report from step 1 when
   one exists for this dispatch — omit it only when this task was
   verified without a subagent:

```bash
adaptive-artifacts create --type project:check-run \
  --subject "<task-slug>" \
  --payload '{"criterion_id":"<acceptance-record-id>","revision":"<git sha or dirty>","result":"pass","effort":"<effort-slug>","method":"manual","signed_by":""}' \
  --rel informed_by:<acceptance-record-id> \
  --rel informed_by:<execution-report-id>
```

   Prefer `git rev-parse HEAD` after a commit. `signed_by` is the
   maintainer's name/handle once they've reviewed a `manual`
   check-run's evidence; leave it `""` only while still awaiting that
   review — a `method=manual` check-run with `signed_by=""` surfaces
   under `handoff`'s Unsigned Manual Check role and stays there until
   someone signs it. When the user signs it, clear the unsigned gate
   at the event (kinds-and-focus, Needs-you clears) — prefer `correct`
   on the existing check-run over rewriting `signed_by` only in a new
   create:

```bash
adaptive-artifacts correct --type project:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

   `tdd`/`check` results (from `aff check`) don't need a
   signer; their `signed_by` stays `""`.

   On every path, `result` is `pass`, `fail`, `blocked`, or
   `insufficient` (contract `payload_enum`).

   - `pass` — the linked requirement was met. Evidence for that
     requirement only. A pass on one requirement does not verify
     another, and a pass of one `evidence_kind` does not cover a
     requirement that was not run.
   - `fail` — the check ran and the requirement was not met. It does
     not say the design is wrong. A failing concurrency test does not
     itself claim the design is wrong.
   - `blocked` — the check could not run.
   - `insufficient` — the criterion was not exercised.

   When the acceptance has `requirement`, the runner (or a `manual`
   create) puts that `requirement` and an `evidence_kind` from the
   contract enum (`unit`, `integration`, `acceptance`, `static`,
   `types`, `security`, `property`, `fuzz`, `review`, `runtime`,
   `other`) on the check-run. Still no `level` and no `next`. A
   structured `manual` create looks like:

```bash
adaptive-artifacts create --type project:check-run \
  --subject "<task-slug>" \
  --payload '{"criterion_id":"<acceptance-record-id>","revision":"<git sha or dirty>","result":"fail","effort":"<effort-slug>","method":"manual","signed_by":"","requirement":"<requirement-id>","evidence_kind":"review"}' \
  --rel informed_by:<acceptance-record-id> \
  --rel informed_by:<execution-report-id>
```

## Assess

Skip this section for simple work (a phase with no specification, and
incidental work). Structured work runs Assess after the check-runs and
before step 5.

Write one `project:assessment` per requirement the check-runs speak
to. Subject is `<phase-slug>-<requirement-id>`. The Reason section
names the cause in words. The check-run does not. Payload:
`requirement`, `status`, `level` (omit only when `status` is
`verified`), `next`, `confidence` (`high` when `verified`, otherwise
`low`), `phase`, `effort`, `missing` (what evidence is absent, or
empty). Body sections, all non-empty: `## Evidence`, `## Missing`,
`## Reason`.

List the active assessment for that subject. Create when there is
none. Supersede when one is active — `supersede` keeps the subject.
Compare with that previous assessment before choosing `level` (see
Evidence escalation below).

```bash
adaptive-artifacts list --type project:assessment --subject "<phase-slug>-<requirement-id>" --state active --full
```

Choose the first `next` from the evidence. Do not send every failure
to execute. Use the first row the evidence supports:

| Evidence | status | level | next |
|---|---|---|---|
| `failed` and the cause is the task's code | `failed` | `implementation` | `execute` |
| `failed` and the design cannot satisfy the requirement | `failed` | `design` | `design` |
| `failed` and no task covers the requirement | `failed` | `plan` | `plan` |
| `failed` and the requirement is ambiguous or contradicted | `failed` | `specification` | `specify` |
| integration-report `fail`, and a task must change | `failed` | `integration` | `execute` |
| integration-report `fail`, otherwise | `failed` | `integration` | `integrate` |
| `insufficient` (the criterion was not exercised) | `insufficient` | `verification` | `verify` |
| `level` `environment` or `unknown` | `blocked` | `environment` or `unknown` | `verify` |
| every check the requirement needs passed | `verified` | omit | `release` |

A row is `failed` when the check-run `result` is `fail` and the cause
column matches. Read the phase integration report before using the
integration rows:

```bash
adaptive-artifacts list --type project:integration-report --where payload.phase=<phase-slug> --full
```

`insufficient`: set `missing` to the absent check. Prefer the first
missing kind in this order: acceptance, integration, unit, property,
fuzz, review. A passing check-run of a different kind does not force
`status` `verified`.

`level` `environment` or `unknown`: the cause is the environment, or
the evidence does not say. Set `next` to `verify`. Do not set `next`
to `execute`. Open a blocking `project:continuity-question` and a
finding with `needs` `human` (the same two writes as a repeated
`specification` below). Leave the work-item `in_progress`.

`failed` and the cause is the task's code: `level` `implementation`,
`next` `execute`. Leave the work-item `in_progress`.

When a verification check fails and the cause is the task's code,
leave the work-item `in_progress` and use assessment `next` `execute`
for that failure. Do not tell the parent to run a suite the
acceptance does not name. Run that acceptance's `verify_command`.

```bash
adaptive-artifacts create --type project:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"failed","level":"implementation","next":"execute","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<check-runs for this requirement and their results>

## Missing

none

## Reason

<the cause in words: the task's code failed the requirement>"
```

Design, plan, and specification use the same create (or supersede)
shape with that row's `status`, `level`, `next`, and `confidence`
`low`. Integration uses `level` `integration` and `next` `execute`
when a task must change, otherwise `next` `integrate`.

```bash
adaptive-artifacts create --type project:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"insufficient","level":"verification","next":"verify","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":"acceptance"}' \
  --body "## Evidence

<which checks ran and which did not>

## Missing

acceptance

## Reason

<the criterion was not exercised>"
```

```bash
adaptive-artifacts create --type project:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"blocked","level":"environment","next":"verify","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":"<absent environment fact, or empty>"}' \
  --body "## Evidence

<the blocked check and the environment fact>

## Missing

<absent environment fact, or none>

## Reason

<environment or unknown; not the task's code>"
```

When `status` is `verified`, omit `level`. `next` is `release`.
`confidence` is `high`. `missing` is empty. For an **oracle-backed**
requirement, write `verified` only after mechanical oracle verify
holds (assertion-level red at base, green at head, hashes match or
approved amendment). Name those facts in `## Evidence`.

```bash
adaptive-artifacts create --type project:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"verified","next":"release","confidence":"high","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<the passing check-runs for this requirement; for oracle-backed: assertion-level red id, green id, hash match or approved oracle-amendment id>

## Missing

none

## Reason

<why the evidence is sufficient for this requirement>"
```

### Evidence escalation

Decision evidence-escalation. Compare this assessment with the
previous one for the same requirement. Stay at the same `level` only
when the new check-runs add evidence (a new `evidence_kind`, a
narrower failing case, or a cause that was unnamed and is now named)
or the previous cause is resolved. Otherwise raise one step on
`implementation` → `design` → `specification`, set `next` to that
stage (`design`, then `specify`), and say in Reason that the evidence
did not increase. Do not use a failure count. `plan` and `integration`
are chosen only when the evidence says so. They are not inserted under
a repeated implementation failure.

A repeat that adds no evidence raises `implementation` to `design`
only in that case. The first implementation failure still uses `next`
`execute`. When the new check-run adds an `evidence_kind`, names a
narrower failing case, or names a cause that was unnamed, supersede
and stay at `implementation` / `execute`. When the previous cause is
resolved and the requirement now passes, `status` is `verified` and
`level` is omitted — that is not a raise.

```bash
adaptive-artifacts supersede --type project:assessment --id <assessment-id> \
  --expected-revision <revision> \
  --payload '{"requirement":"<requirement-id>","status":"failed","level":"design","next":"design","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<previous check-runs and the new ones>

## Missing

none

## Reason

The evidence did not increase. <the same cause, still unnamed beyond the task's code>"
```

When `specification` repeats and the evidence still did not increase,
supersede again with `level` `specification` and `next` `specify`, and
say in Reason that the evidence did not increase. Do not raise further
and do not set `next` to `execute`. Open a blocking
`project:continuity-question` and a finding with `needs` `human`. The
same two writes cover `level` `environment` or `unknown`.

```bash
adaptive-artifacts create --type project:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"assess:<phase-slug>-<requirement-id>"}'

adaptive-artifacts create --type project:finding \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"claim":"<requirement-id> needs a human: specification repeated without new evidence, or the level is environment or unknown","basis":"<the assessments and check-runs>","invalidated_when":"<a new evidence_kind, a named cause, or a human answer>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<the repeated assessment or the environment or unknown level>

## Consequence

<dispatch stays stopped>

## Follow-up

<what the human must answer>"
```

When the user answers the question or decides the finding, clear each
at the event (kinds-and-focus, Needs-you clears):

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>

adaptive-artifacts update --type project:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

### Release

Decision release-ready. `ready` means the evidence is sufficient.
When every assessment for the phase is `verified`, create
`project:release` with `state` `ready`. Read the specification's
`requirements` and the active assessments for the phase; every
requirement id must have an active assessment whose `status` is
`verified`. Do not write `merged`, `deployed`, or any other state in
this skill. Do not deploy.

```bash
adaptive-artifacts list --type project:assessment --where payload.phase=<phase-slug> --state active --full

adaptive-artifacts create --type project:release \
  --subject "<phase-slug>" \
  --payload '{"state":"ready","phase":"<phase-slug>","effort":"<effort-slug>"}'
```

Leave the work-item `in_progress` when any assessment for its
requirements is not `verified`. Go to step 5 only when each of those
assessments is `verified`.

5. On **pass** (simple work: binary gate met, or evaluate finding
   accepted as done; structured work: Assess recorded `verified` for
   each requirement this work-item covers): transition the work-item
   to `done`:

```bash
adaptive-artifacts update --type project:work-item --id <id> \
  --transition done --expected-revision <revision>
```

   The acceptance definition stays `active` (it is a `definition`
   record, not part of the work-item's lifecycle).

   A work-item reaching `done` is not itself proof its criteria were
   met — the lifecycle state alone does not say whether verification
   happened, only that this session declared it over. If you are
   closing to `done` while the criterion's most recent `check-run`
   shows `result=fail` or no `check-run` exists at all (live
   verification deliberately deferred, an accepted risk, or similar),
   that is only legitimate as an explicit call, and it must leave a
   trace a reader can find without decoding "done" — `create --type
   project:finding` on the task subject with `needs":"human"` first,
   naming what was deferred and why, **before** the `update
   --transition done` above:

```bash
adaptive-artifacts create --type project:finding \
  --subject "<task-slug>" \
  --payload '{"claim":"<task-slug> closed done with an unmet or unverified criterion","basis":"<why it was closed anyway>","invalidated_when":"<what would undo this acceptance>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<the failing/missing check-run and why closing proceeded anyway>

## Consequence

<what remains unverified>

## Follow-up

<what someone should do to close the gap, or \"none\">"
```

   This surfaces under `handoff`'s Needs Human role so the gap is
   visible without anyone having to already suspect it.
6. On **fail** for simple work (not the intentional TDD red you will
   fix next): leave the work-item `in_progress`. Optionally create
   `project:continuity-question` on the **focus** subject with
   `blocking=true` if dispatch must stop. Structured work does not
   stop in this step: a `fail` is evidence for Assess, and Assess
   chooses `next`. Do not send every failure to execute. When a
   verification check fails and the cause is the task's code, leave
   the work-item `in_progress` and use assessment `next` `execute`
   for that failure. Do not tell the parent to run a suite the
   acceptance does not name. The parent (`execute-phase`) will
   re-dispatch that task or create a fix work-item under the retry
   budget; this skill does not re-dispatch and does not change
   evidence-escalation routing.
7. On **abandoned** approach: `create --type project:failed-attempt`
   with `attempted_action`, `retry_when`, `effort`. If the whole task
   is dropped (not just this attempt), transition the work-item to
   `withdrawn` instead of `done`:

```bash
adaptive-artifacts update --type project:work-item --id <id> \
  --transition withdrawn --expected-revision <revision>
```

   Otherwise leave it `in_progress` for a retry.
8. Regenerate views (`handoff`, `project:plan`, `project:verification`,
   `project:brief`) and `adaptive-artifacts validate`.

## Close

`close` is the simple-work batch for steps 3-5 (a phase with no
specification, and incidental work). It skips assessment and release.
A result other than `pass` is already unmet there; do not route
`blocked` or `insufficient` through `close`. Structured work gets
check-runs from `aff check` (or a `manual` create) with
`requirement` and `evidence_kind`, then Assess. `close` does not copy
those fields. Use the simple-work batch once every active acceptance
for this work-item has a runner-produced check-run (`tdd`/`check`) or
a judged `manual` result (step 3) and any diagnose/eval records from
step 2 are already written. It still leaves `in_progress` on a `fail`
(step 6) or drives `withdrawn` (step 7) — `close` only covers the
`done` path, including the deliberate "done anyway" path step 5
requires a `finding` for. It **enforces** that requirement instead of
merely stating it: it refuses to build the batch at all — prints which
criteria are unmet and writes nothing — when `transition` is `done`, a
criterion is unmet or was never checked, and no `finding` was given.
It also refuses a pass-only `tdd` `done` close that lacks valid
request-carried red evidence (and has no `finding`). For
oracle-backed `tdd`, close-batch also refuses when frozen
`oracle_hashes` drift without an approved `project:oracle-amendment`,
or when there is no qualifying assertion-level red for the frozen
tests. Do not hand-write the batch to route around a refusal.

For `tdd`/`check`, `aff close-batch` does **not** invent pass/fail or
create check-runs. It only references runner-produced `check_run_id`s
(from `aff check`) and copies each run's `result` for the
refusal gate. For `tdd` on `done`, also carry red-first fields from a
prior runner fail (below) — for oracle-backed acceptances that red
must be assertion-level. `manual` criteria still carry `result` /
`revision` / `signed_by` so the batch can create those check-runs.
`check` and `manual` do not require `red_check_run_id`.

CLI: `aff close-batch` (or `<plugin>/bin/aff close-batch`
after resolving `<plugin>` per [ensure-store.md](../ensure-store.md)).

1. Fetch the active acceptances — superseded ones are retired
   definitions and must not be re-checked:

```bash
adaptive-artifacts list --type project:acceptance --subject "<task-slug>" --state active
```

2. Fetch the most recent execution-report for this dispatch (omit this
   and leave `execution_report_id` `null` below when this task was
   verified without one, per step 1 above):

```bash
adaptive-artifacts list --type project:execution-report --subject "<task-slug>" --full --order-by recorded_at
```

   Take the last entry — `recorded_at` sorts oldest first.
3. For each active acceptance, use step 3's check-runs. For
   `tdd`/`check`, take the runner check-run's `id` and its `result`
   (do not invent a result). For `tdd` closing to `done` with
   `result` `pass`, also list check-runs for the task and pick a
   prior runner-produced fail for that criterion as the red:

```bash
adaptive-artifacts list --type project:check-run --subject "<task-slug>" --full --order-by recorded_at
```

   Copy from the red check-run into the criteria entry:
   `red_check_run_id` (the red run's `id`), `red_result` (must be
   `fail`), `red_revision`, `red_runner` (must be `affidavit`), and
   when `red_revision` is `dirty`, non-empty `red_diff_sha256` from
   that run's `diff_sha256`. Copy the green run's `revision` onto the
   criteria entry too — ancestry requires it when red is a SHA (green
   must equal or be a git descendant of red). Dirty red skips SHA
   ancestry and only needs `red_diff_sha256`. Do not invent red
   fields; if there is no valid red, either keep the work-item
   `in_progress` or use the finding escape below. For `manual`, use
   `revision` from `git rev-parse HEAD` once committed and
   `signed_by` once reviewed. Write a close-request JSON: `criteria`
   holds one entry per acceptance actually checked; `acceptance_ids`
   lists **every** active acceptance from step 1, checked or not, so
   the refusal check can see one that was skipped. Leave `finding`
   `null` when every criterion passed and each `tdd` pass carries
   valid red evidence:

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>", "<acceptance-id-2>"],
  "criteria": [
    {
      "criterion_id": "<acceptance-id-1>",
      "method": "tdd",
      "check_run_id": "<green-runner-check-run-id>",
      "result": "pass",
      "revision": "<green-sha>",
      "red_check_run_id": "<red-runner-check-run-id>",
      "red_result": "fail",
      "red_revision": "<red-sha>",
      "red_runner": "affidavit"
    },
    {"criterion_id": "<acceptance-id-2>", "method": "check", "check_run_id": "<runner-check-run-id-2>", "result": "pass"}
  ],
  "finding": null
}
EOF
```

   When the red was recorded dirty, use `red_revision` `"dirty"` and
   carry `red_diff_sha256` (green `revision` is still copied from the
   green check-run, but dirty red does not run SHA ancestry):

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>"],
  "criteria": [
    {
      "criterion_id": "<acceptance-id-1>",
      "method": "tdd",
      "check_run_id": "<green-runner-check-run-id>",
      "result": "pass",
      "revision": "<green-sha-or-dirty>",
      "red_check_run_id": "<red-runner-check-run-id>",
      "red_result": "fail",
      "red_revision": "dirty",
      "red_runner": "affidavit",
      "red_diff_sha256": "<digest-from-red-check-run-diff_sha256>"
    }
  ],
  "finding": null
}
EOF
```

   When closing anyway on an unmet/unverified criterion, or on a
   `tdd` pass without red evidence, `finding` carries exactly step
   5's fields (`needs` is forced to `"human"` regardless of what is
   written here):

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>"],
  "criteria": [
    {"criterion_id": "<acceptance-id-1>", "method": "check", "check_run_id": "<runner-check-run-id>", "result": "fail"}
  ],
  "finding": {
    "claim": "<task-slug> closed done with an unmet or unverified criterion",
    "basis": "<why it was closed anyway>",
    "invalidated_when": "<what would undo this acceptance>",
    "body": "## Evidence\n\n<the failing/missing check-run and why closing proceeded anyway>\n\n## Consequence\n\n<what remains unverified>\n\n## Follow-up\n\n<what someone should do to close the gap, or \"none\">"
  }
}
EOF
```

4. Build the batch. Pass `--cwd` when the code lives in a phase
   worktree so git-ancestry red-first checks run against that repo
   (default: process cwd):

```bash
aff close-batch \
  --input /tmp/close-request.json \
  --out /tmp/close-batch.ndjson \
  --cwd <repo-or-worktree>
```

   Exit `0` means the batch was written — run `apply` next. Exit `2`
   means refused (unmet/unverified criterion with no `finding`, or
   pass-only `tdd` without valid red evidence / ancestry) — stderr
   names the criteria; go back to step 3, either resolve them, add
   red fields, or add the `finding`, and do **not** run `apply`.
   Exit `1` means the close-request JSON was malformed — fix it and
   retry.
5. Only after a `0` exit, apply the batch — one `project:check-run`
   create per `manual` criterion (each `informed_by` both its
   acceptance and the execution-report); `tdd`/`check` check-runs are
   already in the store from `aff check` and are not
   re-created. Then the `finding` if one was given, then the
   work-item transition, all in one process:

```bash
adaptive-artifacts apply /tmp/close-batch.ndjson
```

6. Regenerate views and validate as step 8 above.

## Do not

- Dual-write CI as records if CI already owns the result
- `create --type project:check-run` for `method` `tdd` or `check` —
  only `aff check` (or an already runner-produced id) may
  supply those binary results
- Invent pass/fail in a close-request for `tdd`/`check` without a
  runner `check_run_id` — `aff close-batch` must reference that id
- Treat a checklist tick as pass without a `check-run` (binary) or
  a `finding` (comparative)
- Transition a work-item to `done` on an unmet or unverified criterion
  without the `finding` from step 5 — a bare `done` must never be the
  only trace of that
- Put a metric table in `check-run.result`
- Leave a `manual` check-run's `signed_by` empty once someone actually
  reviewed it — sign it, or it lingers under Unsigned Manual Check
- Invent `red_*` fields or close a pass-only `tdd` criterion without
  a runner-produced fail preceding the green (or a finding escape) —
  `aff close-batch` refuses that close; verify the actual command
  output and copy ids/fields from real check-runs
- Close another focus's work-item
- Skip `aff close-batch` and hand-assemble the `apply` NDJSON for a
  multi-criterion close — that is exactly the ad-hoc path that let a
  `done` work-item carry a failing check-run with no `finding` before
- Put `level` or `next` on a check-run
- Treat a failing concurrency test as a claim that the design is wrong
- Send every failure to `execute`
- Escalate by a failure count
- Insert `plan` or `integration` under a repeated implementation failure
- Write `project:release` with `state` other than `ready`, or deploy
- Write an assessment or a release for incidental work or a phase with
  no specification
- Tell the parent to run a suite the acceptance does not name
- Edit the tree from a verification task when its check fails. The
  verification executor returns `fail`; leave the work-item
  `in_progress` and use assessment `next` `execute` for that failure
- Route `manual` criteria through `aff check`
- Mark an oracle-backed requirement `verified` without mechanical
  oracle verify (assertion-level red at base, green at head, hashes
  match or approved amendment)
- Invent `oracle_hashes` / amendment status in prose instead of
  reading the acceptance and `project:oracle-amendment` records
