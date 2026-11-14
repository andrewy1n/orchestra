---
name: tasks
description: >-
  Promotes the current phase and materializes the current effort's
  work-item and acceptance records (this phase only, or a single
  incidental task), with depends_on edges between tasks that must
  run in order and a closing verification task for the phase. Use when the user finished a planning conversation,
  engage handed off here, or they asked to generate tasks for the
  focused effort.
---

# Plan the current effort

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md) in the **current work repo**
before writing records. Follow [kinds-and-focus.md](references/kinds-and-focus.md).
Batch example: [record-mechanics.md](references/record-mechanics.md). Skip for
incidental work that fits in the current chat. If handoff has no goal
for the focus, use `init` first (`engage` if kind/focus unset).

## Rules

- Records are plan authority. `orchestra view plan` is derived.
- Materialize **this focus** and **this phase only**. Future phases
  stay placeholder `score:phase` bodies, with no work-items yet.
- Same `subject` (task slug) for a work-item and its acceptance(s).
  `payload.effort` = focus; `payload.phase` = a real `score:phase`
  subject, or `""` for incidental.
- A light phase (payload `weight` `light`) has no specification or
  design: take requirement ids and text from `## Requirements` in the
  phase body. One acceptance may carry `requirements` (a JSON array of
  ids) instead of `requirement` when one check proves them all. A full
  phase keeps one `requirement` per acceptance.
- Several acceptances: first uses task slug; extras use
  `<task-slug>-<short suffix>`. No task slug is a prefix of another.
- `deliver`/`repair` work-items carry atomic requirement ids in
  `requirements` (JSON array of atomic ids; never compound). From specification
  when it exists (also set `decisions`); else id'd list in
  `## Description`. Each acceptance names exactly one id in
  `requirement`. `incidental` may omit; `evaluate` follows campaign
  rules.
- New acceptances are **thin**: omit `criterion` or `""`. Done meaning
  lives on requirement text.
- Choose `method` separately from `oracle_policy`; follow
  [verification-policy.md](references/verification-policy.md). Stamp the
  resolved policy on every new acceptance. Create selected freezes once.
- Write all work-items and acceptances of the phase through one
  `canon apply` call (step 9). Do not run `canon create` one by one for
  them.
- Do not write `conductor:assessment` or `conductor:integration-report`.
- Lifecycle only: `planned` -> `in_progress` -> `done` / `withdrawn`.
  Never write `stage`, `live`, `ready`, or `wave`. This skill creates
  work-items and promotes the phase; `execute` and `verify`
  move work-items.
- Dependencies: `payload.depends_on`, a JSON array of work-item
  subjects, prerequisites created first. Tasks that must rewrite the
  same function get a `depends_on` edge.
- Every `deliver`/`repair` phase ends with a **verification task**
  that `depends_on` every other work-item; at least one acceptance is
  an integration check through the real entry point (not whole-tree
  pilot tests). `evaluate` only with a binary gate; incidental never.
- Every work-item has `## Approach` and `executor` (`inline`|
  `subagent`; missing -> `subagent`; same within a wave), plus `size`
  (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock,
  not padded): XS 2–5, S 5–10, M 8–15, L 15–25, XL 25–40.
  Phase body records session shape (`one sitting` | `more than one`),
  human stops, collision notes, `## Proof`, and `## Landing` (branch
  `phase/<phase-slug>`, worktree `<repo>/.worktrees/<phase-slug>`,
  base `main`). When Landing is present and the phase gate holds,
  commit the phase branch from the phase worktree. Then run
  `orchestra land --phase <phase-slug>`. Land runs `orchestra gate`
  first and runs the land adapter only when the gate holds. The
  Landing section names branch, worktree, base and repo only.
  `orchestra.toml` `[land]` and `[suite]` configure the adapter and
  the suite. Merge stays human. On a non-zero exit, stop and ask. No
  Landing -> not ready for plan review. Incidental has none.
- Decisions change via `supersede`, never `update` to `superseded`.
  Never supersede another subject's goal or position.
- Parent writes records. Only subagent here: phase-scoped
  **oracle-author** (step 8, selected frozen acceptances), tests only, no
  `canon`. Parent runs the tests and writes the freeze fields in the
  acceptance create. Never hand Approach / implementation hints to the
  oracle-author. Frozen tdd requires assertion-level red; frozen check does not.

## Steps

0. When handed an assessment with `next: plan`, consume it before a
   fresh full plan. Add the missing task(s) for the uncovered
   requirement ([task-shapes.md](references/task-shapes.md)), write
   them through one `canon apply`, and re-open plan review for
   the delta (step 11 question, `plan-review:<phase-slug>`). Stop until
   the user approves. No `next: plan` assessment: continue with step 1.
1. Run `orchestra handoff` if the handoff is not in context. Resolve
   **focus** and **kind**. Read `orchestra view plan --effort <focus>`.
2. If this focus has no `score:effort`, create it (`init` step 6) for
   **this subject only**. If closed, reopen first (kinds-and-focus).
   Resolve current phase: named in context, else `in_progress`, else
   lowest-`ordinal` `planned`; ask if several fit. `engage` `phase:
   new` -> create in step 3 with `ordinal` = max existing + 1.
   Approach must be settled (a `score:decision` for this phase, or
   fixed in chat); else `spec` or ask to skip. Incidental
   skips the settle check.
3. Promote the current phase to `in_progress` with its real plan
   (`canon get --type score:phase`, then `update --transition
   in_progress --body-file`). The body has real `## Problem`,
   `## Approach`, `## Exit criteria`, `## Proof`, and `## Landing`,
   plus size, human stops, and collision notes. `## Proof`: `kind`
   (`demo`|`commands`|`claims`|`audit-triage`|`mixed`) + one sentence
   on look intent. Landing holds no merge command, suite command,
   push, pull request, or store commit on the default branch. Missing
   phase record -> `create` first (`init` step 7). Skip for
   incidental. Write a phase `score:position` (`scope` `phase`) only
   for a note a person must read; progress is derived. Leave the
   effort position alone until the phase closes.
4. For each durable choice, `create --type score:decision` (`choice`,
   `alternatives`, `phase`, `effort`; body `## Rationale` /
   `## Counter-argument`). Skip trivia.
5. Draft the independent tasks (or the one incidental), 6. the
   dependent tasks (`depends_on` in the payload), and 7. the
   verification task last (`deliver`/`repair`). Shapes are in
   [task-shapes.md](references/task-shapes.md). Drafting writes no
   record.
8. Oracle author: skip when no acceptance selects `frozen`. Otherwise
   follow [oracle-author.md](references/oracle-author.md) before creating
   selected frozen acceptances. Unfrozen tdd tests can start during execution.
9. Write the batch. Put every drafted record in one NDJSON file and
   run `canon apply` once (line shape and example in
   [record-mechanics.md](references/record-mechanics.md)). Order the lines: each
   prerequisite work-item before the work-items that list it in
   `depends_on`, the verification task last, a work-item before its
   acceptances. On `"ok": false`, fix the failed lines and apply only
   those. Never re-apply lines that succeeded. After the apply, run `orchestra check --acceptance <acceptance-id> --cwd
   <repo-or-worktree>` for each oracle-backed acceptance. The runner
   records evidence: expect red for frozen tdd; frozen check needs no red.
10. Run `canon validate`. Show the user the focus task list
    (`orchestra view plan --effort <focus>`) and which exit criterion
    each acceptance covers.
11. Open the plan review gate (skip incidental). Do not open until:
    each work-item has `## Approach`; wave executors agree; the phase
    body has size, human stops, collision notes, `## Proof`, and
    `## Landing`; and each selected frozen acceptance has
    non-empty `test_ids` and `oracle_hashes`. Run `orchestra analyze
    <phase-slug>` first. Refuse plan review while it exits 1. Fix each
    error finding, then run it again. If the effort has no `autonomy`,
    run `orchestra effort autonomy <focus> auto-plan` first: the default
    is to approve the task plan. If the effort's `autonomy` is
    `auto-plan` or `auto-phases`, skip the gate and go to `execute`.
    Only an explicit `gated` creates a blocking
    `score:continuity-question` with scope
    `plan-review:<current-phase-slug>`. Ask approve / change / send back to
    `spec`. On approval, answer the question and record a task review with
    authority `user-approval`. For `auto-plan` or `auto-phases`, record a
    task review with authority `task-plan-policy` before execution.
