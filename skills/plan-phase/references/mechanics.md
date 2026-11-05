# plan-phase mechanics

Full step-by-step mechanics. SKILL.md keeps the judgment; this file is the manual fallback and the record of every contract.

## Plan the current effort

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
- A light phase (payload `weight` `light`) has no specification or
  design: take requirement ids and text from `## Requirements` in the
  phase body, and one acceptance may carry `requirements` (a JSON
  array of ids) instead of `requirement` when one check proves them
  all. A full phase keeps one `requirement` per acceptance.
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
- An oracle-backed acceptance is created once, with `test_ids` and
  `oracle_hashes` in the same create. Never create it and then update
  it to freeze. Run the oracle author (step 8) before the batch.
- Write all work-items and acceptances of the phase through one
  `canon apply` call (step 9). Do not run `canon create` one by one for
  them.
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
  base `main`). When Landing is present and the phase gate holds,
  commit the phase branch from the phase worktree. Then run
  `orchestra land --phase <phase-slug>`. Land runs `orchestra gate`
  first and runs the land adapter only when the gate holds. The
  Landing section names branch, worktree, base and repo only.
  `orchestra.toml` `[land]` and `[suite]` configure the adapter and
  the suite. Merge stays human. On a non-zero exit, stop and ask. No
  Landing → not ready for plan review. Incidental has no Landing.
- Decisions change via `supersede`, never `update` to `superseded`.
- Parent writes records. Only subagent here: phase-scoped
  **oracle-author** (step 8, deliver/repair) — tests only, no
  `canon`. Parent runs the tests and writes the freeze fields in the
  acceptance create. Never hand Approach / implementation hints to the
  oracle-author. Freeze only after assertion-level red.
- Never supersede another subject's goal or position.

## Steps

0. When handed an assessment with `next: plan` (or engage routes here
   for that), consume before a fresh full plan: list those
   assessments, add missing task(s) for the uncovered requirement
   (shapes in [task-shapes.md](references/task-shapes.md), including
   `depends_on` and a verification-task edge via `update --payload`
   with the full `depends_on` array when needed; write the new
   records through one `canon apply`, step 9), re-open plan review
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
   sentence on look intent.    `## Landing`: branch
   `phase/<phase-slug>`, worktree `<repo>/.worktrees/<phase-slug>`,
   base `main`. When Landing is present and the phase gate holds,
   commit the phase branch from the phase worktree. Then run
   `orchestra land --phase <phase-slug>`. Land runs `orchestra gate`
   first and runs the land adapter only when the gate holds. Landing
   names branch, worktree, base and repo only. Do not write a merge
   command, a suite command, a push, a pull request, or a store
   commit on the default branch into Landing. `orchestra.toml`
   `[land]` and `[suite]` configure them. On a non-zero exit, stop
   and ask. Missing phase record →
   `create` first (`init` step 7), then `update`. Skip for incidental.

   Write a phase `score:position` (`subject` = phase slug, `scope`
   always `phase`) only for a note a person must read, such as a human
   stop or a collision warning. Phase progress is derived from
   work-item states; do not write a position for it. Update a note
   with `supersede`. Leave the effort position alone until the phase
   closes.

```bash
canon create --type score:position \
  --subject "<phase-slug>" \
  --payload '{"position":"<note a person must read>","scope":"phase","effort":"<effort-slug>","phase":"<phase-slug>"}'
```

4. For each durable choice, `create --type score:decision` with
   `choice`, `alternatives`, `phase`, `effort` and body
   `## Rationale` / `## Counter-argument`. Skip trivia.
5. Independent tasks (or the one incidental): draft work-item +
   acceptance(s) — see [task-shapes.md](references/task-shapes.md)
   (Independent task). Drafting writes no record.
6. Dependent tasks: draft with `depends_on` in the payload — see
   [task-shapes.md](references/task-shapes.md) (Dependent task).
7. Verification task last (`deliver`/`repair`) — see
   [task-shapes.md](references/task-shapes.md) (Verification task).
8. Oracle author (`deliver`/`repair` only) — see
   [oracle-author.md](references/oracle-author.md). It runs before any
   acceptance exists. Its result fills `test_ids` and `oracle_hashes`
   in the drafted acceptances.
9. Write the batch. Put every drafted record in one NDJSON file and
   run `canon apply` once. Each line is `{"op":"create","type":...,
   "subject":...,"payload":{...},"body":...}` (`body` only for a
   work-item). Order the lines: each prerequisite work-item before the
   work-items that list it in `depends_on`, the verification task
   last, and a work-item before its acceptances. Example with one
   oracle-backed acceptance:

```bash
cat > /tmp/plan-batch.ndjson <<'EOF'
{"op":"create","type":"score:work-item","subject":"<task-slug>","payload":{"title":"<short title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":["R1"],"decisions":["<decision>"]},"body":"## Description\n\nR1: <observable behavior>\n\n## Approach\n\n<implementation recipe>"}
{"op":"create","type":"score:acceptance","subject":"<task-slug>","payload":{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1","test_ids":["tests/test_<area>.py::test_<case>"],"oracle_hashes":["tests/test_<area>.py:sha256:<hex>"]}}
{"op":"create","type":"score:work-item","subject":"verify-<phase-slug>","payload":{"title":"Verify <phase title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":["R1"],"decisions":["<decision>"],"depends_on":["<task-slug>"]},"body":"## Description\n\nProve the phase exit criteria hold together.\n\n## Approach\n\n<implementation recipe>"}
{"op":"create","type":"score:acceptance","subject":"verify-<phase-slug>","payload":{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<integration test command>","requirement":"R1"}}
EOF
canon apply /tmp/plan-batch.ndjson
```

   `canon apply` prints `{"ok", "applied", "failed", "results"}`. It
   does not stop at a failed line: later lines still run, and a line
   that depends on a failed line fails too. On `"ok": false`, print
   each failed entry of `results` and the input line with the same
   `line` number. Fix the failing line, then apply a file that holds
   only the failed lines in the same order. Never re-apply lines that
   succeeded.
   After the apply, run `orchestra check --acceptance <acceptance-id>
   --cwd <repo-or-worktree>` for each oracle-backed acceptance. The
   runner records the red check-run that close needs; expect `fail`.
10. Validate:

```bash
canon validate
```

11. Show the user the focus task list (`orchestra view plan --effort <focus>`), with the verification task and
    which exit criterion each of its acceptances covers. Query
    `derived.ready`/`wave` directly if useful (plan view omits them):

```bash
canon list --type score:work-item \
  --where payload.effort=<effort-slug> --where payload.phase=<current-phase-slug>
```

12. Open the plan review gate (skip incidental). Do not open until:
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

    The effort's `autonomy` skips this gate at `auto-plan` and
    `auto-phases`; `gated` or a missing level keeps it.
    Ask approve / change / send back to `settle-phase`. Change tasks
    on request. On approval, answer the question; only then may
    `execute-phase` run:

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```
