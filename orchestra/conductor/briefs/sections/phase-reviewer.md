## Reviewer

Reviewer writes no store records. Parent creates them.

1. Build the restricted brief:
   `orchestra review-brief --phase {phase} --base <base> --phase-head <phase-head>`
   It refuses while the suite policy is unmet at the phase head: no
   `{phase}-suite` check-run, or a failed one under
   `gate=required`. A fix task moves the head, so run the suite again
   at the new head before the reviewer starts.
   (work-item Description/Approach, acceptances, requirements/
   invariants, `git diff <base>..<phase-head>` only — no
   execution-report, check-run, assessment, or assignment text).
2. Host `reviewer` if available; else read-only/explore subagent
   with the reviewer prompt in this brief. Refuse reviewer
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
  --subject "{phase}-review" \
  --payload '{"criterion_id":"{phase}-review","revision":"<phase-head-sha>","result":"<pass|fail>","effort":"{effort}","method":"review","signed_by":"","evidence_kind":"review"}' \
  --body "<reviewer output, verbatim>"

canon create --type tuner:finding \
  --subject "review-<task-or-phase>-<kind>" \
  --payload '{"claim":"<kind> on <task>: <expected>","basis":"<observed>","invalidated_when":"fix lands and reviewer re-run passes, or human clears","effort":"{effort}","needs":"<none|human>"}' \
  --body "## Evidence

<expected vs observed from the finding>

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Create a fix work-item under the retry budget, or answer Needs you."
```

4. Fixable blocking findings (`spec-gap`, `behavior-bug`, `missing-test`,
   `invariant-violation`, except `severity: judgment`) → fix
   work-items using the retry rules in this brief and
   `retry_max_fix_tasks`. Never reopen `done`. After fixes verify,
   re-run the reviewer **once** on the new diff. Budget exhausted →
   Needs-you path; stop.
5. One `conductor:integration-report` from the reviewer's `integration`
   map. Skip when incidental or no multi-task implementation wave.
   `pass` only when verdict is `PASS` and those sections hold — a
   clean git merge is not enough.

```bash
canon create --type conductor:integration-report \
  --subject "{phase}" \
  --payload '{"phase":"{phase}","effort":"{effort}","result":"<pass|fail|blocked>","revision":"<phase-head-sha>"}' \
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
