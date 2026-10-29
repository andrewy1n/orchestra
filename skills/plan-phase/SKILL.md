---
name: plan-phase
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
Do not copy this plugin into the project.

Skip for incidental work that fits in the current chat and is not an
interrupt. If handoff has no goal for the focus and the user is not
ready to specify tasks, use `init` first (`engage` if kind/focus unset).

## Rules

- Records are plan authority. `orchestra view plan` is derived.
- Materialize **this focus** only; for `deliver`/`repair`/`evaluate`,
  **this phase only**. Future phases stay placeholder `score:phase`
  bodies — no work-items yet.
- Same `subject` (task slug) for a work-item and its acceptance(s).
  `payload.effort` = focus; `payload.phase` = current phase slug (must
  match a real `score:phase` subject) or `""` for incidental.
- Several acceptances: first uses task slug; extras use
  `<task-slug>-<short suffix>`. Do not pick a task slug that is a
  prefix of another in the same phase.
- `deliver`/`repair` work-items carry atomic requirement ids in
  `requirements` (JSON array of atomic ids; never compound). From specification
  when it exists (also set `decisions`); else id'd list in
  `## Description`. Each acceptance names exactly one id in
  `requirement`. `incidental` may omit; `evaluate` follows campaign
  rules.
- New acceptances are **thin**: omit `criterion` or `""`. Done meaning
  lives on requirement text, not a re-summary field.
- Do not write `conductor:assessment` or `conductor:integration-report`.
- Lifecycle only: `planned` → `in_progress` → `done` / `withdrawn`.
  Never write `stage`, `live`, `ready`, or `wave`. This skill creates
  work-items and promotes the phase to `in_progress`. `execute-phase`
  and `verify-work` move work-items to `in_progress` and `done`.
- Dependencies: `payload.depends_on`, a JSON array of work-item
  subjects. Create each prerequisite first; canon rejects an unknown
  subject. `derived.ready` / `derived.wave` are engine-computed —
  never write them.
- Every `deliver`/`repair` phase ends with a **verification task**
  that `depends_on` every other work-item; acceptances cover exit
  criteria; at least one is an integration check through the real
  entry point (not whole-tree / unfiltered pilot tests). `evaluate`
  only when the campaign has a binary gate; incidental never.
- Every work-item has `## Approach` and `executor` (`inline`|
  `subagent`; missing → `subagent`; same within a wave), plus `size`
  (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock,
  not padded). Guidance: XS 2–5, S 5–10, M 8–15, L 15–25, XL 25–40.
  Phase body records session shape (`one sitting` | `more than one`),
  human stops, collision notes, `## Proof`, and `## Landing` (branch
  `phase/<phase-slug>`, worktree `<repo>/.worktrees/<phase-slug>`,
  base `main`, close actions; push only as a human stop). No Landing
  → not ready for plan review. Incidental has no Landing.
- Decisions change via `supersede`, never `update` to `superseded`.
- Parent writes records. Only subagent here: phase-scoped
  **oracle-author** (step 8, deliver/repair) — tests only, no
  `canon`. Parent runs `orchestra check` and freezes
  fields. Never hand Approach / implementation hints to the
  oracle-author. Freeze only after assertion-level red.
- Never supersede another subject's goal or position.

## Steps

0. When handed an assessment with `next: plan` (or engage routes here
   for that), consume before a fresh full plan: list those
   assessments, add missing task(s) for the uncovered requirement
   (shapes in [task-shapes.md](references/task-shapes.md), including
   `depends_on` and a verification-task edge via `update --payload`
   with the full `depends_on` array when needed), re-open plan review
   for the delta:

```bash
canon list --type conductor:assessment --state active \
  --where payload.phase=<current-phase-slug> --where payload.next=plan

canon create --type score:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:<current-phase-slug>"}'
```

   On approval, clear at the event; stop until then — do not dispatch:

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   No `next: plan` assessment → continue with step 1.

1. Run `orchestra handoff` if the handoff is not in context. Resolve
   **focus** and **kind**. Read `orchestra view plan --effort <focus>`.
2. If this focus has no `score:effort`, create it (`init` step 6) for
   **this subject only**. If closed, reopen first (kinds-and-focus).
   Resolve current phase: named in context, else `in_progress`, else
   lowest-`ordinal` `planned` — never `score:position` `scope`.
   If several fit and none named, ask. `engage` `phase: new` → create
   in step 3 with `ordinal` = max existing + 1. Approach must be
   settled (a `score:decision` for this phase, or fixed in chat);
   else `settle-phase` or ask to skip. Skip settle check for incidental.

```bash
canon list --type score:decision --where payload.phase=<current-phase-slug> --state active
```

3. Promote the current phase to `in_progress` with its real plan:

```bash
canon get --type score:phase --id <phase-id>
```

   If `planned`, replace placeholder body and transition:

```bash
canon update --type score:phase --id <phase-id> \
  --transition in_progress \
  --expected-revision "<revision>" \
  --body-file "<phase-plan.md>"
```

   `<phase-plan.md>` has real `## Problem`, `## Approach`, `## Exit
   criteria`, `## Proof`, and `## Landing`. Record size (`one sitting`
   | `more than one`), human stops, collision notes. `## Proof`:
   `kind` (`demo`|`commands`|`claims`|`audit-triage`|`mixed`) + one
   sentence on look intent. `## Landing`: branch
   `phase/<phase-slug>`, worktree `<repo>/.worktrees/<phase-slug>`,
   base `main`, close actions (commit phase branch → merge `main` →
   store commit); push only as a human stop. Missing phase record →
   `create` first (`init` step 7), then `update`. Skip for incidental.

   Then create this phase's position (`subject` = phase slug,
   `scope` always `phase`). Update during the phase with `supersede`.
   Leave the effort position alone until the phase closes.

```bash
canon create --type score:position \
  --subject "<phase-slug>" \
  --payload '{"position":"<what this phase is doing now>","scope":"phase","effort":"<effort-slug>","phase":"<phase-slug>"}'
```

4. For each durable choice, `create --type score:decision` with
   `choice`, `alternatives`, `phase`, `effort` and body
   `## Rationale` / `## Counter-argument`. Skip trivia.
5. Independent tasks (or the one incidental): create work-item +
   acceptance(s) — see [task-shapes.md](references/task-shapes.md)
   (Independent task).
6. Dependent tasks: create with `depends_on` in the payload — see
   [task-shapes.md](references/task-shapes.md) (Dependent task).
7. Verification task last (`deliver`/`repair`) — see
   [task-shapes.md](references/task-shapes.md) (Verification task).
8. Oracle author (`deliver`/`repair` only) — see
   [oracle-author.md](references/oracle-author.md).
9. Validate:

```bash
canon validate
```

10. Show the user the focus task list (`orchestra view plan --effort <focus>`), with the verification task and
    which exit criterion each of its acceptances covers. Query
    `derived.ready`/`wave` directly if useful (plan view omits them):

```bash
canon list --type score:work-item \
  --where payload.effort=<effort-slug> --where payload.phase=<current-phase-slug>
```

11. Open the plan review gate (skip incidental). Do not open until:
    each work-item has `## Approach`; wave executors agree; phase body
    has size, human stops, collision notes, `## Proof`, and
    `## Landing`; and for deliver/repair each intended oracle-backed
    tdd acceptance has non-empty `test_ids` and `oracle_hashes`.
    Run the analyze check first:

```bash
orchestra analyze <phase-slug>
```

    Refuse plan review while it exits 1. Fix each error finding, then
    run it again.

```bash
canon create --type score:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:<current-phase-slug>"}'
```

    Ask approve / change / send back to `settle-phase`. Change tasks
    on request. On approval, answer the question; only then may
    `execute-phase` run:

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```
