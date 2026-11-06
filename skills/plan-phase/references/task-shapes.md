# Task shapes (work-item + acceptance)

Use from plan-phase steps 5–7. List the phase specification first:

```bash
canon list --type score:specification --where payload.phase=<current-phase-slug> --state active
```

For every `deliver` / `repair` task, payloads include `requirements`
(atomic ids this task implements) and each acceptance's `requirement`
(exactly one of those ids). When a `score:specification` exists,
take id texts from it and set `decisions` to the decision subjects the
task follows. When none exists, write the id'd list in `## Description`
and still stamp `requirements` / `requirement`. Omit `criterion` (or
`""`) — thin acceptances. Several acceptances use
`<task-slug>-<short suffix>`. `incidental` may omit `requirements`,
`decisions`, and `requirement`.

Every `canon create` below shows one line of the plan batch. Write
the lines through one `canon apply` (plan-phase step 9), not one by
one. Follow [verification-policy.md](verification-policy.md). Stamp the
resolved `oracle_policy` on every acceptance. A selected frozen acceptance
carries `test_ids` and `oracle_hashes` in its create payload.

## Independent task

Put the Description in `body` of the batch line.

```bash
canon create --type score:work-item \
  --subject "<task-slug>" \
  --payload '{"title":"<short title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":["R1","R2"],"decisions":["<decision-a>","<decision-b>"]}' \
  --body "## Description

R1: <observable behavior>
R2: <observable behavior>

## Approach

<implementation recipe>"

canon create --type score:acceptance \
  --subject "<task-slug>" \
  --payload '{"method":"tdd","oracle_policy":"none","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1"}'

canon create --type score:acceptance \
  --subject "<task-slug>-perf" \
  --payload '{"method":"check","oracle_policy":"none","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command that proves R2>","requirement":"R2"}'
```

For selected frozen acceptances, use the complete example in
[oracle-author.md](oracle-author.md). Ordinary tdd needs no freeze fields. Drop the second acceptance when there is only one
requirement. A task needs at least one `score:work-item` and one
`score:acceptance`.

Set `kind` and `phase` from the effort (`phase` is `""` when
incidental). Set `executor` to `inline` or `subagent` (same within a
wave). Every new work-item includes `size` and `estimate_minutes`.
`method` is `tdd`, `check`, or `manual`; `verify_command` is the
literal command (empty string for `manual` with no script).

- `repair` — `verify_command` proves repro-gone plus a regression
  check, not "we investigated." Diagnose happens at execute/verify.
- `evaluate` — the campaign is the binary gate when there is one
  (`method=check`). Comparative / inconclusive lives in a finding at
  verify, not in `method`.
- `incidental` — one observable done-check; usually `check` or
  `manual`; exempt from atomic requirement ids.

## Dependent task

Needs another same-phase task done first. Create the prerequisite
first, then list its subject in `depends_on`:

```bash
canon create --type score:work-item \
  --subject "<task-slug>" \
  --payload '{"title":"<short title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":["R1","R2"],"decisions":["<decision-a>","<decision-b>"],"depends_on":["<prerequisite-task-slug>"]}' \
  --body "## Description

R1: <observable behavior>
R2: <observable behavior>

## Approach

<implementation recipe>"

canon create --type score:acceptance \
  --subject "<task-slug>" \
  --payload '{"method":"tdd","oracle_policy":"none","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R1"}'
```

## Verification task

For a `deliver` or `repair` phase, create last, with every other
work-item subject in `depends_on`. One thin acceptance per exit
criterion (suffixed subjects), each naming exactly one requirement id.
Acceptances come from phase exit criteria; at least one is an
integration check through the real entry point. A `verify_command`
that runs the whole `tests` tree, or `tests/dashboard/test_web_dashboard.py`
without a `-k` filter for this phase, is not a verification
acceptance.

Use distinct exit requirements, such as R3 and R4 below. Do not attach a downstream acceptance to a prerequisite task's requirement: that prerequisite cannot close until all its acceptances pass.

```bash
canon create --type score:work-item \
  --subject "verify-<phase-slug>" \
  --payload '{"title":"Verify <phase title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":["R3","R4"],"decisions":["<decision-a>","<decision-b>"],"depends_on":["<task-slug-1>","<task-slug-2>"]}' \
  --body "## Description

Prove the phase exit criteria hold together: run the integration
check through the real entry point, then every other phase check.

## Approach

<implementation recipe>"

canon create --type score:acceptance \
  --subject "verify-<phase-slug>" \
  --payload '{"method":"check","oracle_policy":"none","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<integration test command>","requirement":"R3"}'

canon create --type score:acceptance \
  --subject "verify-<phase-slug>-<criterion-suffix>" \
  --payload '{"method":"check","oracle_policy":"none","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R4"}'
```

A task that later joins the phase gets a `depends_on` edge on the
verification task so the gate still waits for it. Update the
verification work-item's `depends_on` with the full array:

```bash
canon update --type score:work-item --id <verification-work-item-id> \
  --expected-revision <revision> \
  --payload '{"depends_on":["<task-slug-1>","<task-slug-2>","<new-task-slug>"]}'
```
