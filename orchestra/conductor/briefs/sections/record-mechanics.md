# Record mechanics

Only the parent session writes the shared store. Use `canon` and
`orchestra`; never edit record files by hand.

## Plan records

- Put phase requirement ids in each `deliver` or `repair` work-item's
  `requirements` array. Keep each id atomic.
- Put one acceptance on each requirement it verifies. Use one acceptance with
  a `requirements` array only when one check proves every listed requirement.
- Put task dependencies in `depends_on` as work-item subjects. Create the
  prerequisite before its dependents.
- Give each work-item `## Description`, `## Approach`, `executor`, `size`, and
  `estimate_minutes`. Every wave uses one executor type.
- Put all work-items and acceptances in one ordered NDJSON batch. Create the
  phase verification task last. It depends on every other phase task.
- Run `canon validate` after applying the batch.

## TDD and checks

An acceptance names the literal `verify_command`. `orchestra check` writes
runner evidence for `tdd` and `check`. Never create those check-runs by hand.

For `tdd`, record a failing run before the passing run. Close-batch needs the
runner-produced red and green ids. The green revision must equal or descend
from the red revision. A dirty red also needs its diff hash.

Frozen-oracle acceptances require assertion-level red and matching hashes at
green. Never edit frozen oracle files or invent freeze fields.

## Execute and close

`orchestra wave start` selects the lowest ready wave. It writes `in_progress`,
`assignee`, and `write_root`. Dispatch only tasks whose derived `ready` is
true. Return evidence as JSON; the parent writes records.

`orchestra task land <task> --evidence <file>` commits the task worktree,
writes its execution report, and runs active acceptance checks. Use
`orchestra close-batch` for the verified close request, then `canon apply`.
Never reopen a done task. Create a dependent fix task instead.

End each passing wave with `orchestra wave end`. Do not merge branches by
hand. Keep check-runs, findings, and execution reports as separate evidence.
