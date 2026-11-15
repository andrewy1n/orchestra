## Phase gate

Run `orchestra gate {phase}`. Exit 0 means the gate holds. Exit 1
lists each missing term. Exit 2 means a usage, unknown phase or config
error. Add `--cwd <phase-worktree>` to check that worktree's HEAD. Do not judge the gate from the queries below
when the command is available.

The gate holds only when all terms are true (skip review/suite terms
for incidental):

- Verification task exists and is `done`
- Every active phase acceptance: latest check-run per `criterion_id`
  passes, and a passing runner check-run at phase-head SHA
- Every latest `method=manual` check-run has `signed_by`
- Passing `method: review` / `evidence_kind: review` at phase-head
- When `suite.gate` in `orchestra.toml` is `required` (and mode ≠ `none`):
  passing `{phase}-suite` at that same phase-head SHA.
  `advisory` fail does not block; `deferred` / `none` → skip
- No active `tuner:finding` for the effort has `needs` `human`

Fallback for reading the records by hand:

```bash
canon list --type score:work-item \
  --where payload.effort={effort} --where payload.phase={phase}

canon list --type score:acceptance \
  --where payload.effort={effort} --where payload.phase={phase}

canon list --type tuner:check-run \
  --where payload.criterion_id=<acceptance-id> --order-by recorded_at

canon list --type tuner:check-run \
  --where payload.method=review --where payload.effort={effort} \
  --order-by recorded_at

canon list --type tuner:check-run \
  --where payload.evidence_kind=integration --where payload.effort={effort} \
  --order-by recorded_at

canon list --type tuner:finding --where payload.effort={effort} \
  --where payload.needs=human
```

User signs an unsigned manual check:

```bash
canon correct --type tuner:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

Gate fails → leave phase `in_progress`, name what is missing, stop.
Do not waive suite policy. `deliver`/`repair` always need verification
+ passing review at head.
