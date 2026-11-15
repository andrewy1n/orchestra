## Suite

After analyze exits 0 and before the reviewer starts. The suite runs at
the phase head, so the review and the suite name the same revision. Do not
waive suite policy — a human changes `[suite]` in the root
`orchestra.toml` instead. Load with `orchestra suite policy`. An omitted
`[suite]` section or `mode=none` → skip.
`mode=external` or `gate=deferred` → do not run locally (`deferred` =
Landing human stop). For `smoke`/`full` with a `command`: run via
`orchestra suite start` / `poll` / `collect` / `cancel` / `record` in the phase
worktree; one check-run at phase-head SHA, subject
`{phase}-suite`, `evidence_kind: integration`, with runner
metadata. Dirty-only pass refused like `orchestra check`. Suite is
never red-first.

`suite start` returns an immutable `run_id`. Pass it to `poll`, `collect`,
and `record` when you inspect an older run. Add `--timeout <seconds>` to
bound a run. Cancel with `orchestra suite cancel --run-id <run_id>`.
The `--session` option remains a job label.

After a local run:

- `gate=required` — missing/failing suite blocks merge. On fail, fix
  work-items under retry budget (one subject per failing module);
  never reopen `done`; no inline fix-and-rerun; re-run suite at new
  head after fixes; budget exhausted → Needs you. Create the fix
  work-items before the reviewer starts. The reviewer never sees a head
  with a failing required suite.
- `gate=advisory` — record check-run; on fail also a finding; do not
  block merge; no fix-task storm.
- `gate=deferred` — no local run; Landing human stop.

When the suite fails, re-run each failing test id in a clean `main`
worktree. Label every id `new` or `pre-existing` in the check-run basis
or finding. A `pre-existing` label does not change the gate: `required`
still blocks and `advisory` still does not. Put the pre-existing ids in
front of the user; do not wait silently.

For an orphaned worker, inspect the run's `worker.log`, `result.json`, and
`output.log` under `.suite/jobs/`. Older `.suite/<label>.log` and
`.suite/<label>.exit` files are diagnostic only. Do not signal saved PIDs.
Do not fix-and-rerun inside this step.

```bash
orchestra suite record \
  --phase "{phase}" \
  --effort "{effort}" \
  --cwd <phase-worktree> \
  --run-id "<run-id>"

canon create --type tuner:finding \
  --subject "suite-advisory-{phase}" \
  --payload '{"claim":"advisory suite fail for {phase}-suite","basis":"<exit_code and failing node ids>","invalidated_when":"suite check-run passes at phase head, or human clears","effort":"{effort}","needs":"none"}' \
  --body "## Evidence

<suite output tail>

## Consequence

Advisory only — Landing is not blocked by this suite fail.

## Follow-up

Fix opportunistically or clear the finding; do not open a required-gate fix-task storm."
```

Advisory finding only when `gate=advisory` and the suite failed.
