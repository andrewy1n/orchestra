---
name: execute
description: >-
  Dispatch ready work-items within the selected phase scope and land their
  evidence. Use when the workflow routes to execute.
---

# Execute tasks

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md),
[kinds-and-focus.md](references/kinds-and-focus.md), and
[record-mechanics.md](references/record-mechanics.md). Follow
[retry-loop.md](references/retry-loop.md) for interrupted work and
[execute-mechanics.md](references/execute-mechanics.md) for task dispatch.
Follow [verification-policy.md](references/verification-policy.md) when
checking frozen oracle evidence. All frozen changes require a parent-approved oracle amendment.
For manifest claims, follow the signed manifest and verdict path in the verification policy.

## Own

- Dispatch only ready work-items in the requested phase scope.
- Record execution evidence through task landing.
- Integrate passing task branches at each wave boundary.
- Stop after the selected execution step. Verification stays separate.

## Steps

1. Resolve the focus and selected phases from the handoff. Read
   `orchestra view plan --effort <focus>` and blocking questions for that
   effort. Do not dispatch another effort or work blocked by an open plan
   review. Retry eligible `in_progress` tasks first.
2. Run:

```bash
orchestra wave start <phase-slug>
```

   Dispatch only the lowest ready wave. Stop if executors disagree, no task is
   ready, or a task branch conflicts while refreshing the phase tip.
3. Follow each task brief verbatim. A subagent receives only its assigned
   write root, brief, scope, constraints, frozen oracle paths, and kind
   instruction. Subagents return evidence as JSON. They never write the store
   or `.canon/`. Inline work follows the same boundary.
4. Land each task with `orchestra task land`. It commits the task branch,
   records the report, and runs active acceptance checks. On a non-zero result,
   stop and follow verify; do not merge that branch.
5. Run `orchestra wave end <phase-slug>`. Do not resolve merge conflicts or
   merge task branches by hand. A merge conflict opens a blocking question;
   leave it unresolved and stop.
   When tasks need competing behavior, leave the question open and ask the user.
6. Continue ready waves only while the selected operation includes execute.
   After the last passing wave, report what landed and hand off to verify.

## Do not

- Dispatch when `derived.ready` is false
- Recompute wave numbers or expand selected phase scope
- Write execution reports from chat memory
- Close tasks directly or reopen a done task
- Edit frozen oracle files or create runner check-runs by hand
- Resolve a merge conflict outside `orchestra wave resolve`
- Run reviewer, suite, phase gate, proof packet, or phase closure here
