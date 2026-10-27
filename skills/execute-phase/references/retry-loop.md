# Retry loop

Parent-only. Run at the start of each dispatch cycle, before the
planned ready `list` in execute-phase step 2. Evidence escalation
still chooses `level` / `next`; the budget only decides when to stop.

## Re-dispatch selection

```bash
canon list --type score:work-item --state in_progress \
  --where payload.effort=<focus> --where payload.phase=<current-phase-slug>
```

For each result, load the latest `conductor:assessment` (structured) or
latest `tuner:check-run` (simple). Retry when assessment `next` is
`execute`, or check-run `result` is `fail`. Skip a task whose executor
is still running for the current assignment, or that has an open
blocking `continuity-question` with `scope` `retry:<task-slug>`.

Re-dispatch with the same `payload.executor` as the prior wave
(`inline` or `subagent`; missing means `subagent`). Do not change mode.

## Budget (hard backstop)

Defaults (override in the phase body's run facts):

- `retry_max_redispatches`: 2 re-dispatches per task
- `retry_time_multiplier`: 2 (stop when cumulative executor time
  ≥ 2× `estimate_minutes` when set; count or time, whichever first)
- `retry_max_fix_tasks`: 3 fix work-items created for the phase

Omit a key → use the default. If cumulative time cannot be computed
from assignment / execution-report timestamps, use re-dispatch count
only. `attempts` is that count (absent → 0).

When a per-task or per-phase fix-task budget is exhausted, do not
re-dispatch. Open Needs you and stop selecting it:

```bash
canon create --type score:continuity-question \
  --subject "<focus>" \
  --payload '{"owner":"user","blocking":true,"scope":"retry:<task-slug>"}'

canon create --type tuner:finding \
  --subject "retry-<task-slug>" \
  --payload '{"claim":"retry budget exhausted for <task-slug> after <attempts> re-dispatches","basis":"<attempts, check-runs, assessments>","invalidated_when":"human raises the budget or withdraws the task","effort":"<focus>","needs":"human"}' \
  --body "## Evidence

<attempts, failing check-runs, latest assessment>

## Consequence

Dispatch of this task stops until the human answers.

## Follow-up

Raise the run-fact budget, withdraw the task, or choose another approach."
```

When the user answers or clears the finding, clear at the event
(kinds-and-focus, Needs-you clears):

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>

canon update --type tuner:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'
```

## Amendment, attempts, re-dispatch

For each retryable task still inside budget: record an
`assignment-amendment` whose `## Correction` quotes the failing
check-run evidence (runner output tail) and the assessment's
`## Reason` when present; set `attempts` to prior+1 (absent → 0, so
first re-dispatch writes `1`); create a fresh `conductor:assignment`
and dispatch as in execute-phase steps 4–5 (same executor mode).
Work-item stays `in_progress` — never reopen `done`.

```bash
canon create --type conductor:assignment-amendment \
  --subject "<task-slug>" \
  --payload '{"assignment":"<task-slug>","effort":"<focus>"}' \
  --body "## Correction

Re-dispatch after failure.

## Failing check-run

<runner output tail from the failing check-run>

## Reason

<assessment ## Reason when present, else omit>"

canon update --type score:work-item --id <id> \
  --expected-revision <revision> \
  --payload '{"attempts":1}'

canon create --type conductor:assignment \
  --subject "<task-slug>" \
  --payload '{"work_item":"<task-slug>","executor":"<assignee>","effort":"<focus>"}' \
  --body "## Orientation

Re-dispatch attempt <attempts>. Same territory and executor mode as the prior wave.

<quoted work-item Description/Approach, requirement texts by id, design, and decisions as in step 4>"
```

Then dispatch with that mode through execution-report + `verify-work`.

## Fix tasks (closing verification)

When the closing verification task fails and the cause is another
task's code, create a new fix work-item in the same phase — never
reopen `done`. The fix has no `depends_on`. Approach comes from the
failure; acceptance is the failing check. Then add the fix's subject to
the verification task's `depends_on` (send the full array) so
`derived.ready` re-gates verification. Count against `retry_max_fix_tasks`. If that budget is
exhausted, use the budget-exhaustion Needs-you path above
(`scope: retry:<verification-slug>` or `retry:<fix-slug>`) instead.

```bash
canon create --type score:work-item \
  --subject "fix-<failing-area>" \
  --payload '{"title":"Fix <failing area>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<focus>","executor":"<same mode as phase wave>","size":"S","estimate_minutes":8,"requirements":["<id>"],"decisions":["<decision-subject>"]}' \
  --body "## Description

Fix the failure that blocked closing verification.

## Approach

<from the failing check-run / node ids>"

canon create --type score:acceptance \
  --subject "fix-<failing-area>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<focus>","verify_command":"<command>","requirement":"<id>"}'

canon update --type score:work-item --id <verification-work-item-id> \
  --expected-revision <revision> \
  --payload '{"depends_on":["<existing-dependency-slug>","<fix-work-item-slug>"]}'
```

Never transition a `done` work-item back to `in_progress` or
`planned`. Fix tasks stay in the current phase.
