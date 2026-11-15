## Do not

- Write a plan document as authority
- Let subagents write records (any executor mode) — store is single-writer
- Restate `criterion` / verify_command / findings in the dispatch prompt, or
  paraphrase work-item / requirement claims — brief owns the quotes
- Write a `conductor:assignment`; the `in_progress` update carries
  `assignee`, `write_root`, `dispatch_id`, and `dispatch_started_at`
- Write a phase `score:position` for progress; write one only for a
  human-readable note
- Skip `conductor:execution-report` and derive check-runs from chat memory
- Ask for an implementation recipe when `## Approach` is present
- Spawn a subagent for `inline`, or spawn when the wave disagrees on executor
- Dispatch when `derived.ready` is false, or another focus's work
- Write or recompute `ready`/`wave`
- Load the whole store; route by focus, then phase
- Close a phase only when its phase-end gate holds
- Write integration-report `pass` from a clean git merge alone, or write
  it before closing verification / reviewer, or invent its body
- Call the phase complete (or merge) without a proof-packet at phase-head
  when code or claims changed
- Merge without passing review at phase-head, or without required suite
  at phase-head when `suite.gate` is `required`
- Waive / skip / override configured suite policy in `orchestra.toml`
- Let the reviewer call `canon` or write `.canon`
- Re-run the reviewer more than once after fix tasks for the same phase-end
- Fix-and-rerun inside the suite step (`required` → fix tasks + re-run at
  new head; `advisory` → finding only)
- Create a branch or worktree without Landing; create a task branch or
  task worktree for the work-item that depends_on every other phase
  work-item; let code leave the worktree when Landing is present;
  write `.canon` off the primary checkout or include it in a task
  commit
- Skip the per-task commit when Landing is present and that task's
  code changed; create an empty commit when there is nothing to commit
- Rebase a task branch, merge a task branch whose check did not pass,
  resolve a task-branch merge conflict by any path other than
  `orchestra wave resolve`, or start the next wave while that conflict
  is unresolved
- Do not resolve a merge conflict outside `orchestra wave resolve`
- Do not push from phase close
- Tell the executor to avoid `git add -A`
- Let the verification executor edit the tree
- Reopen `done` — create a fix work-item and `depends_on` instead
- Re-dispatch after retry budget exhaustion without `scope: retry:<task-slug>`
- Skip the retryable `in_progress` pass
- Put a whole-suite command on a per-task `verify_command`
- Let an executor edit frozen oracle files or write
  `tuner:oracle-amendment`; or `create`/`correct` a task check-run
  with method `tdd`/`check` (those come from `orchestra check`). Suite
  (`orchestra suite record`) and `manual`/`review` stay parent writes
- Let a subagent sign an amendment or write `test_ids` / `oracle_hashes`


## Do not (moved from SKILL.md)

- Re-dispatch after retry budget exhaustion without `scope:
  retry:<task-slug>`; skip the retryable `in_progress` pass
- Put a whole-suite command on a per-task `verify_command`; let the
  reviewer call `canon`
