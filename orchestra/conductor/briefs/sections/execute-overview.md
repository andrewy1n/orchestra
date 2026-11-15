## Execute the focused effort

Requires `canon` and `orchestra` on PATH and a live
orchestra store. Follow `verify`
after each task finishes (subagent return or inline).

**Single-writer:** only this parent may write via `canon`.
Subagents never write — including under any future `--read-only`
executor mode (that mode names what may be *read*; a subagent write
would race `--expected-revision`).

Task lifecycle is `planned -> in_progress -> done` (or `withdrawn`).
Orchestra moves a work-item to `in_progress` (step 4) and to `done`
(`verify`). The planner creates work-items.
`derived.ready` / `derived.wave` are engine-computed from `depends_on`
— never write them.

Each dispatch is recorded by the `in_progress` update of the
work-item (it carries `assignee`, `write_root`, a unique `dispatch_id`,
and UTC `dispatch_started_at`) and by a `conductor:execution-report`
(evidence verbatim). Landing records elapsed seconds for that dispatch.
Executors may report `tokens_total` only when they know a reliable total;
zero is valid, and absent stays absent. Write no
`conductor:assignment`. Executors take method / verify_command /
findings / constraints from `orchestra brief <task-slug>`. The brief
renders `## Orientation`: it quotes (verbatim, by id) work-item
Description/Approach, linked requirement text, design
Invariants/Assumptions, and named decisions. The dispatch prompt adds
territory and concurrency notes only. Do not paraphrase claims or
treat empty/legacy `criterion` as the lead claim.

Write a phase `score:position` only for a human-readable note. Phase
progress is derived from work-item states. The effort position still
changes at phase close.
