---
name: execute-phase
description: >-
  Dispatches orchestra work-items whose derived.ready is true, in
  dependency order, each wave inline in this session or as one
  subagent per task, recording an execution-report per dispatch. Parent session writes records; subagents return
  evidence only. Use when the user asks to execute a phase, run
  ready work, or continue after engage.
---

# Execute the focused effort

Requires `canon` and `orchestra` on PATH and a live orchestra store.
If missing, follow [ensure-store.md](references/ensure-store.md) then
`init` (if no goal for the focus) and `plan-phase`. Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Follow
`verify-work` after each task finishes.

Call `orchestra wave start`, `orchestra task land`, and `orchestra wave
end`. Do not run the git and canon steps by hand. The by-hand steps
are the manual fallback in [mechanics.md](references/mechanics.md).

**Single-writer:** only this parent may write via `canon`. Subagents
never write, in any executor mode. They return evidence as a JSON block.

Task lifecycle is `planned -> in_progress -> done` (or `withdrawn`).
`wave start` moves a work-item to `in_progress`; `task land` moves it
to `done` when every requirement it covers is verified. Never write
`derived.ready` / `derived.wave`. Each dispatch is recorded by the
`in_progress` update (`assignee`, `write_root`) and a
`conductor:execution-report` (evidence verbatim). Executors take
method, verify_command, findings, and constraints from the brief.

## Steps

1. Run `orchestra handoff` if the handoff was not injected. Resolve
   **focus**. Read `orchestra view plan --effort <focus>` and blocking
   `continuity-question`s for that subject. Do not dispatch while a
   blocking question is open on this focus (`plan-review:<phase-slug>`
   gates only that phase), or another effort's tasks. Before planned
   ready work, re-dispatch retryable `in_progress` items:
   [retry-loop.md](references/retry-loop.md).
2. Start the wave:

```bash
orchestra wave start <phase-slug>
```

   It picks the ready planned work-items of the lowest wave. It refuses
   a wave whose tasks disagree on `payload.executor` and names them:
   stop, do not dispatch. With `## Landing` in the phase body, it
   creates or reuses the task branches and worktrees and merges the
   phase tip in; the task that depends on every other phase task runs
   in the phase worktree. Without Landing, work stays in the current
   checkout. It prints each task's brief. A merge conflict at
   re-dispatch is a blocking `continuity-question`: do not start the
   next wave. If no task is ready, point to `plan-phase`. Follow
   `## Approach`; do not ask the user for a recipe.
3. Dispatch by the shared `payload.executor`.

   **`subagent`:** one `generalPurpose` subagent per task, in parallel
   within the wave. Give each only: the write root, task
   `subject`/title, `kind`, focus `effort`; the brief, verbatim;
   territory and concurrency notes; the frozen oracle paths when any;
   and the kind instruction (`deliver`/`incidental`: implement;
   `repair`: reproduce, observe, name root cause, then fix;
   `evaluate`: run the campaign, return metrics). The verification
   task runs phase checks, returns `fail`, and does not edit the tree.
   The executor returns the evidence JSON and never calls `canon` or
   edits `.canon/`. **`inline`:** this session implements with the
   same brief and lands the evidence the same way.

   **Frozen oracle:** if an acceptance is oracle-backed (non-empty
   `test_ids` and `oracle_hashes`), add the "Frozen oracle (do not
   edit)" section from [mechanics.md](references/mechanics.md) to the
   prompt, listing those paths. Omit it when none is oracle-backed.
   Pushback is an oracle amendment, never a silent rewrite. Only the
   parent adds a signed amendment in `.tuner/manifest.json`, then runs
   `orchestra verify verdict --cwd <repo-or-worktree> --at <revision>
   <claim-id>`. Non-zero means not done: leave `in_progress`.
4. Land each task. Save the executor's evidence JSON to a file
   (`orchestra task land --schema` prints the schema). Treat it as the
   record, not raw material; re-run checks when cheap.

```bash
orchestra task land <task-slug> --evidence <file>
```

   It commits the worktree (excluding `.canon`), writes the
   execution-report, runs every active acceptance, and closes the
   work-item only when the close policy passes (red-first, oracle freeze,
   verified requirements, verdict `pass`, no `needs_human`). Exit 1 means
   a failed check or refusal; exit 3 means a human decision is pending.
   Stop on non-zero. Findings and manual or suite check-runs stay parent writes.
5. For a mid-flight term change, message the subagent and record a
   `conductor:assignment-amendment` ([mechanics.md](references/mechanics.md)).
6. End the wave:

```bash
orchestra wave end <phase-slug>
```

   It merges each passing task branch into `phase/<phase-slug>` in
   task-slug order, in the phase worktree, and never a branch whose
   checks did not pass. On a conflict it stops, leaves the conflict
   unresolved, opens a blocking `continuity-question` with scope
   `merge:<task-slug>`, and exits non-zero. Do not edit the markers, do
   not abort the merge, and do not start the next wave. Otherwise go to
   step 2. After the last wave, run the closing verification task.
7. When no same-focus `planned`/`in_progress` work-items remain (or
   incidental is closed), follow [phase-end.md](references/phase-end.md):
   closing verification, analyze, reviewer, integration-report, suite,
   phase gate, proof packet, phase close. Skip reviewer and suite for
   incidental. An empty task list is not proof the phase is done.
   When Landing is present and the phase gate holds, commit the phase
   branch from the phase worktree. Then run `orchestra land --phase
   <phase-slug>`. Land runs `orchestra gate` first. Ask the user before
   you run land, unless an active constraint authorizes it. On a
   non-zero exit, stop and ask. Do not merge the phase branch by hand.
   Do not push from phase close.
8. After a phase closes, read the effort's `autonomy`. At `auto-phases`,
   plan and promote the next phase without asking (`plan-phase`); at
   `gated` and `auto-plan`, ask first. At every level, stop for a failed
   check, a needs-human finding, a push, or a merge.
9. Run `canon validate`. Record-versus-bind commands: [mechanics.md](references/mechanics.md).

## Do not

- Write a plan document as authority, a `conductor:assignment`, or a
  phase `score:position` for progress; let subagents write records
- Restate `criterion` / verify_command / findings in the dispatch
  prompt, or paraphrase work-item / requirement claims
- Skip `conductor:execution-report` or derive check-runs from chat
- Dispatch when `derived.ready` is false or another focus's work;
  write or recompute `ready`/`wave`; load the whole store
- Close a phase whose gate does not hold; write integration-report
  `pass` from a clean git merge alone or before closing verification /
  reviewer; call the phase complete or merge without a proof-packet,
  passing review, or the required suite at phase-head; waive suite
  policy; re-run the reviewer more than once after fix tasks
- Create a branch or worktree without Landing, or a task branch or
  worktree for the task that depends on every other phase task; write
  `.canon` off the primary checkout or in a task commit
- Rebase a task branch, merge one whose check did not pass, or
  resolve a merge conflict
- Let the verification executor edit the tree; reopen `done` (create a
  fix work-item and `depends_on` instead)
- Let an executor edit frozen oracle files, sign an amendment, or write
  `test_ids` / `oracle_hashes`; `create`/`correct` a task check-run
  with method `tdd`/`check` (those come from `orchestra check`)
