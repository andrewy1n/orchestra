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
work-item (it carries `assignee` and `write_root`) and by a
`conductor:execution-report` (evidence verbatim). Write no
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
