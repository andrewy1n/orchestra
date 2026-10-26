# Assess (structured work)

Skip for simple work (no phase specification, and incidental).
Structured work runs Assess after check-runs and before verify-work
step 5.

Write one `run:assessment` per requirement the check-runs speak
to. Subject is `<phase-slug>-<requirement-id>`. Reason names the
cause in words — the check-run does not. Payload: `requirement`,
`status`, `level` (omit only when `status` is `verified`), `next`,
`confidence` (`high` when `verified`, else `low`), `phase`, `effort`,
`missing`. Body sections, all non-empty: `## Evidence`, `## Missing`,
`## Reason`.

List the active assessment for that subject. Create when none;
supersede when one is active (`supersede` keeps the subject). Compare
with the previous assessment before choosing `level` (see Evidence
escalation).

```bash
canon list --type run:assessment --subject "<phase-slug>-<requirement-id>" --state active --full
```

Choose the first `next` the evidence supports. Do not send every
failure to execute:

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

A row is `failed` when check-run `result` is `fail` and the cause
column matches. Read the phase integration report before using
integration rows:

```bash
canon list --type run:integration-report --where payload.phase=<phase-slug> --full
```

`insufficient`: set `missing` to the absent check. Prefer first
missing kind: acceptance, integration, unit, property, fuzz, review.
A passing check of a different kind does not force `verified`.

`environment` / `unknown`: `next` is `verify`, never `execute`. Open
a blocking `plan:continuity-question` and a finding with
`needs` `human` (same two writes as repeated `specification` below).
Leave work-item `in_progress`.

`failed` and cause is the task's code: `level` `implementation`,
`next` `execute`. Leave `in_progress`. When a verification check
fails for that reason, same routing — do not tell the parent to run a
suite the acceptance does not name; run that acceptance's
`verify_command`.

```bash
canon create --type run:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"failed","level":"implementation","next":"execute","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<check-runs for this requirement and their results>

## Missing

none

## Reason

<the cause in words: the task's code failed the requirement>"
```

Design, plan, and specification use the same create/supersede shape
with that row's fields and `confidence` `low`. Integration uses
`level` `integration` and `next` `execute` when a task must change,
otherwise `next` `integrate`.

```bash
canon create --type run:assessment \
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
canon create --type run:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"blocked","level":"environment","next":"verify","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":"<absent environment fact, or empty>"}' \
  --body "## Evidence

<the blocked check and the environment fact>

## Missing

<absent environment fact, or none>

## Reason

<environment or unknown; not the task's code>"
```

When `status` is `verified`, omit `level`; `next` is `release`;
`confidence` is `high`; `missing` is empty. For **oracle-backed**
requirements, write `verified` only after mechanical oracle verify
holds; name those facts in `## Evidence`.

```bash
canon create --type run:assessment \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"requirement":"<requirement-id>","status":"verified","next":"release","confidence":"high","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<the passing check-runs for this requirement; for oracle-backed: assertion-level red id, green id, hash match or approved oracle-amendment id>

## Missing

none

## Reason

<why the evidence is sufficient for this requirement>"
```

## Evidence escalation

Compare with the previous assessment for the same requirement. Stay
at the same `level` only when new check-runs add evidence (new
`evidence_kind`, narrower failing case, or a cause now named) or the
previous cause is resolved. Otherwise raise one step on
`implementation` → `design` → `specification`, set `next` to that
stage (`design`, then `specify`), and say in Reason that the evidence
did not increase. Do not escalate by failure count. `plan` and
`integration` only when the evidence says so — not under a repeated
implementation failure.

First implementation failure still uses `next` `execute`. When the
previous cause is resolved and the requirement passes → `verified`,
omit `level`.

```bash
canon supersede --type run:assessment --id <assessment-id> \
  --expected-revision <revision> \
  --payload '{"requirement":"<requirement-id>","status":"failed","level":"design","next":"design","confidence":"low","phase":"<phase-slug>","effort":"<effort-slug>","missing":""}' \
  --body "## Evidence

<previous check-runs and the new ones>

## Missing

none

## Reason

The evidence did not increase. <the same cause, still unnamed beyond the task's code>"
```

When `specification` repeats without new evidence, supersede again
with `level` `specification` / `next` `specify`; do not raise further
or set `next` `execute`. Open a blocking continuity-question and a
finding with `needs` `human` (same for `environment` / `unknown`):

```bash
canon create --type plan:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"assess:<phase-slug>-<requirement-id>"}'

canon create --type aff:finding \
  --subject "<phase-slug>-<requirement-id>" \
  --payload '{"claim":"<requirement-id> needs a human: specification repeated without new evidence, or the level is environment or unknown","basis":"<the assessments and check-runs>","invalidated_when":"<a new evidence_kind, a named cause, or a human answer>","effort":"<effort-slug>","needs":"human"}' \
  --body "## Evidence

<the repeated assessment or the environment or unknown level>

## Consequence

<dispatch stays stopped>

## Follow-up

<what the human must answer>"
```

When the user answers or decides the finding, clear at the event
(kinds-and-focus, Needs-you clears):

```bash
canon update --type plan:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>

canon update --type aff:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

## Release

When every assessment for the phase is `verified`, create
`run:release` with `state` `ready`. Every specification
requirement id must have an active `verified` assessment. Do not
write `merged`, `deployed`, or any other state. Do not deploy.

```bash
canon list --type run:assessment --where payload.phase=<phase-slug> --state active --full

canon create --type run:release \
  --subject "<phase-slug>" \
  --payload '{"state":"ready","phase":"<phase-slug>","effort":"<effort-slug>"}'
```

Leave the work-item `in_progress` when any assessment for its
requirements is not `verified`. Go to verify-work step 5 only when
each of those assessments is `verified`.
