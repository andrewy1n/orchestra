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

Requires `artifact-runtime` and `adaptive-artifacts` on PATH. Follow
[ensure-store.md](../ensure-store.md) in the **current work repo**
before writing records. Follow [kinds-and-focus.md](../kinds-and-focus.md).
Do not copy this plugin into the project.

Skip this skill for incidental work that fits in the current chat and
is not an interrupt. If handoff has no goal for the focus and the
user is not ready to specify tasks, use `init` first (`engage` if
kind/focus are unset).

## Rules

- Records plus the derived `project:plan` view are the plan authority.
- Materialize **this focus** only. For `deliver` / `repair` /
  `evaluate`, materialize **this phase only**. Future phases stay
  `project:phase` records with placeholder bodies (from `init`) — no
  work-items for them yet.
- Same `subject` (task slug) for a work-item and its acceptance(s).
  `payload.effort` is the focus on both. `payload.phase` is the
  current phase's slug (must match a real `project:phase` subject —
  `validate` checks this against the whole store); `""` for incidental.
- A task can have several acceptance criteria. Give the first the
  task slug as `subject`; give any additional ones `<task-slug>-<short
  suffix>` (e.g. `checkout-fix-perf`). Two active records of the same
  type sharing one exact `subject` fail `validate` (the current-claim
  identity check has no scope field to distinguish them) — the suffix
  avoids the collision while `list --subject <task-slug>` (exact-or-
  prefix match) still finds the whole family. Do not pick a task slug
  that is itself a prefix of another task's slug in the same phase.
- Every `deliver` or `repair` work-item carries one or more **atomic**
  requirement ids in payload `requirements` (comma-separated). Each
  id names one observable behavior — never a compound id (no commas
  inside an id, no "and"-bundled surfaces, no multiple observables
  under one Rn). When a `project:specification` exists for the phase,
  those ids come from the specification; set `decisions` to the
  comma-separated decision subjects the task follows. When no
  specification exists, the work-item `## Description` **is** the
  id'd list (`R1: …`, `R2: …`), and `requirements` still lists those
  same ids. `incidental` work stays exempt (may omit `requirements`
  and acceptance `requirement`). `evaluate` follows campaign rules.
- Each acceptance for `deliver` / `repair` names exactly one of those
  ids in payload `requirement`. One acceptance per id. That id must
  appear on its work-item. Compound ids in `requirement` are refused
  by skill lint. Several acceptances keep the subject-suffix rule
  above.
- New acceptances are **thin**: omit `criterion` or set it to `""`.
  Do not write criterion prose. Done meaning lives on the requirement
  text (specification `## Requirements`, or the work-item Description
  when there is no spec), not on a re-summary field. `decisions` may
  still be omitted when the task follows none.
- Do not write `project:assessment` or `project:integration-report`
  from this skill.
- Task state is the work-item's **lifecycle** — `planned` (default) ->
  `in_progress` -> `done`, or `withdrawn`. Never write `stage`, `live`,
  `ready`, or `wave` — they don't exist in this contract.
- Dependencies are `depends_on` **relationships**, set with `--rel
  depends_on:<work-item-id>` when a task in this phase can't start
  until another one finishes. `derived.ready` / `derived.wave` are
  computed by the engine from that graph at read time — never write
  them, and never hand-assign a wave number.
- `capture --bundle project:specified-work` cannot carry `--rel` (a
  bundle part is `{type, subject, payload, body}` only). Use the
  bundle for a task with no dependency; for a task that depends on
  another, `create` its work-item directly with `--rel depends_on:...`
  and `create` its acceptance(s) as separate plain calls (still same
  subject convention).
- Every `deliver` or `repair` phase ends with one **verification
  task**: a work-item that `depends_on` every other work-item in the
  phase. Its acceptances cover each exit criterion in the phase body,
  one or more per criterion. The verification task's acceptances come
  from the phase exit criteria, and one is an integration check
  through the real entry point (CLI, service, UI), not a unit test.
  At least one acceptance is an integration check through the real
  entry point. A `verify_command` that runs the whole `tests` tree,
  or `tests/test_dashboard_app.py` without a `-k` filter for this
  phase, is not a verification acceptance. The same rule rejects
  another pre-existing pilot file unless a `-k` filter limits it to
  the tests this phase added. A phase whose exit criteria no
  acceptance checks is not planned yet. `evaluate` phases need it
  only when the campaign has a binary gate; incidental work never
  has one.
- Each new work-item body includes `## Approach`, the implementation
  recipe, and payload `executor` is `inline` or `subagent`. Every task
  in a wave uses the same executor. Missing `executor` means
  `subagent`. Every new work-item payload includes `size` and
  `estimate_minutes`. `size` is `XS` a trivial or local change, `S` a
  small change, `M` a moderate change, `L` a substantial or multi-file
  change, or `XL` a large or high-risk change. `estimate_minutes` is a
  non-negative integer for that task's executor. It is agent wall-clock
  minutes for that worker, not human pacing — do not pad for reading,
  meetings, or context-switch. Typical ranges (guidance only): `XS`
  2–5, `S` 5–10, `M` 8–15, `L` 15–25, `XL` 25–40. Absent means unset.
  Zero is a real estimate. A missing executor means the minutes are
  for a subagent. `size` and `estimate_minutes` are not derived from
  each other. The phase record stores neither field. Inline minutes
  in a wave add. A subagent wave's elapsed estimate is the longest
  `estimate_minutes` among its tasks. Phase elapsed time adds those
  wave figures in wave order. Blank estimates are skipped. A wave
  whose estimates are all blank has no elapsed estimate. The phase
  body still records session shape as `one sitting` or `more than one`.
- The phase body records size as `one sitting` or `more than one`,
  the human stops, and the areas parallel tasks share (collision
  notes). Do not open the plan-review question until the recipe, the
  shared executor, and these phase run facts are present.
- The phase body includes a `## Landing` section with branch
  `phase/<phase-slug>`, worktree
  `<repo-parent>/<repo-name>--<phase-slug>`, base `main`, and these
  close actions: commit code on the phase branch, merge that branch
  into `main`, then commit the store on the primary checkout. Push
  appears only when it is one of the human stops. Incidental work has
  no Landing section. A phase body that omits Landing is not ready
  for plan review.
- Current-claims (`decision`) change via `supersede` (new id), never
  `update` to `superseded`, never payload-only `update`.
- Parent writes records. Do not spawn subagents here, **except** the
  one phase-scoped **oracle-author** subagent in step 8 (deliver /
  repair only). That subagent writes test files only; it does not
  call `adaptive-artifacts`. The parent alone runs `aff check`,
  freezes `test_ids` / `oracle_hashes`, and derives `verify_command`.
- Oracle author ≠ executor: never hand the oracle-author Approach,
  implementation recipes, or code-under-test hints — original
  requirement / specification text only.
- Freeze only after an **assertion-level** red (`aff check` fail whose
  check-run is assertion-level, not import/collection noise). An
  acceptance with non-empty `test_ids` and `oracle_hashes` is
  **oracle-backed**. `test_ids` is comma-separated pytest node ids;
  `oracle_hashes` is comma-separated `relpath:sha256:<hex>` for the
  files those ids live in.
- Never supersede another subject's goal or position.

## Steps

0. When handed an assessment with `next: plan` for this phase (or
   engage routes here because Assess chose `plan`), consume that
   signal before a fresh full plan: list active assessments with
   `next` `plan` for the phase, identify the uncovered requirement,
   add the missing task(s) for that requirement (same create shapes
   as steps 5–7, including `depends_on` and a new edge on the
   verification task via `update --rel` when needed), regenerate
   views, and re-open plan review for the delta. Do not invent a
   parallel skill.

```bash
adaptive-artifacts list --type project:assessment --state active \
  --where payload.phase=<current-phase-slug> --where payload.next=plan
```

   After the missing work-item(s) and acceptance(s) exist, open (or
   re-create if the prior plan-review was already answered) the plan
   review gate:

```bash
adaptive-artifacts create --type project:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:<current-phase-slug>"}'
```

   When the user approves the delta, clear it at the event:

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

   Then stop until approval; do not dispatch. If there is no `next:
   plan` assessment, continue with step 1.

1. Read views if not already in context:
   `adaptive-artifacts hook-start`
   Resolve **focus** and **kind**. Use the `## <focus>` plan section.
2. If this focus has no `active-goal`, create it (`init` step 6) for
   **this subject only**. If its goal is closed, reopen it first
   (kinds-and-focus, Closing and reopening). Resolve the current phase's slug by querying
   `project:phase` for this effort (`--where payload.effort=<focus>`)
   and taking the one named in context (by `engage` or the user), else
   the one that is `in_progress`, else the lowest-`ordinal` `planned`
   one. Several phases of one effort may be `in_progress` at once (one
   chat each); if more than one fits and none is named, ask — never
   `current-position.payload.scope`, which is a stable per-subject
   value, not the phase slug (incidental has no phase). If `engage`
   handed off `phase: new`, the current phase is a new one: create it
   in step 3 with `ordinal` = highest existing ordinal for this effort
   plus one.
   Check that the approach is settled: at least one
   `project:decision` with `payload.phase` = this phase, or the user
   fixed the approach in this chat. If neither, run `discuss` first,
   or ask the user whether to skip it. Skip this check for incidental.

```bash
adaptive-artifacts list --type project:decision --where payload.phase=<current-phase-slug> --state active
```

3. Promote the current phase to `in_progress` with its real plan.
   `Get` its record to check lifecycle and `revision`:

```bash
adaptive-artifacts get --type project:phase --id <phase-id>
```

   If it's `planned` (created by `init`, or new here), replace the
   placeholder body and transition it in one call:

```bash
adaptive-artifacts update --type project:phase --id <phase-id> \
  --transition in_progress \
  --expected-revision "<revision>" \
  --body-file "<phase-plan.md>"
```

   `<phase-plan.md>` has real `## Problem`, `## Approach`, `## Exit
   criteria`, and `## Landing` sections now — this body is the phase's
   plan of record. In that body, record size as `one sitting` or
   `more than one`, the human stops, and the areas parallel tasks
   share (collision notes). The `## Landing` section names branch
   `phase/<phase-slug>`, worktree
   `<repo-parent>/<repo-name>--<phase-slug>`, base `main`, and these
   close actions: commit code on the phase branch, merge that branch
   into `main`, then commit the store on the primary checkout. Push
   appears only when it is one of the human stops.
   If the phase record doesn't exist yet, `create --type project:phase`
   first (`init` step 7 shape), then run the `update` above with the
   revision `create` returned. Skip this step entirely for incidental
   (no phase record).

   Then create this phase's own position, so a chat on another phase
   of the same effort never overwrites it. `subject` is the phase
   slug; `scope` is always `phase`:

```bash
adaptive-artifacts create --type project:current-position \
  --subject "<phase-slug>" \
  --payload '{"position":"<what this phase is doing now>","scope":"phase","effort":"<effort-slug>","phase":"<phase-slug>"}'
```

   Update it during the phase with `supersede`. Leave the effort
   position (`subject` = focus) alone until the phase closes.
4. For each durable choice from planning, `create --type
   project:decision` with `choice`, `alternatives`, `phase`, `effort`
   payload and a `--body-file` with `## Rationale` / `##
   Counter-argument` sections. Skip trivia.
5. For each **independent** task in this phase (or the one incidental
   task), capture work-item + acceptance(s) together — bodies inline
   since `capture` takes JSON, not a file flag; keep the Description
   short here and use plain `create --body-file` instead if it needs
   more than a few lines.

   List this phase's specification first. For every `deliver` /
   `repair` task, the capture and `create` payloads below include
   `requirements` (atomic ids this task implements) and each
   acceptance's `requirement` (exactly one of those ids). When a
   `project:specification` exists, take the id texts from it and set
   `decisions` to the decision subjects the task follows. When none
   exists, write the id'd list in `## Description` and still stamp
   `requirements` / `requirement` the same way. Omit `criterion` (or
   use `""`) — thin acceptances. Several acceptances keep the
   `<task-slug>-<short suffix>` subject. `incidental` may omit
   `requirements`, `decisions`, and `requirement`.

```bash
adaptive-artifacts list --type project:specification --where payload.phase=<current-phase-slug> --state active
```

```bash
adaptive-artifacts capture --bundle project:specified-work --records "$(cat <<'EOF'
[
  {
    "type": "project:work-item",
    "subject": "<task-slug>",
    "payload": {
      "title": "<short title>",
      "phase": "<current-phase-slug>",
      "kind": "deliver",
      "assignee": "",
      "effort": "<effort-slug>",
      "executor": "subagent",
      "size": "M",
      "estimate_minutes": 10,
      "requirements": "R1,R2",
      "decisions": "<decision-a>,<decision-b>"
    },
    "body": "## Description\n\nR1: <observable behavior>\nR2: <observable behavior>\n\n## Approach\n\n<implementation recipe>"
  },
  {
    "type": "project:acceptance",
    "subject": "<task-slug>",
    "payload": {
      "method": "tdd",
      "phase": "<current-phase-slug>",
      "effort": "<effort-slug>",
      "verify_command": "<command that proves R1>",
      "requirement": "R1"
    }
  },
  {
    "type": "project:acceptance",
    "subject": "<task-slug>-perf",
    "payload": {
      "method": "check",
      "phase": "<current-phase-slug>",
      "effort": "<effort-slug>",
      "verify_command": "<command that proves R2>",
      "requirement": "R2"
    }
  }
]
EOF
)"
```

   Drop the second acceptance object entirely when there's only one
   requirement — the bundle just needs at least one `work-item` and at
   least one `acceptance`, not exactly one of each.

   Set `kind` and `phase` from the effort (`phase` is `""` when
   incidental). Set `executor` to `inline` or `subagent`. Every task
   in a wave uses the same executor. Every new work-item payload
   includes `size` and `estimate_minutes`. `method` is `tdd`, `check`, or
   `manual`; `verify_command`
   is the literal command (empty string for `manual` with no script).

   - `repair` — `verify_command` proves repro-gone plus a regression
     check, not "we investigated." Diagnose happens at execute/verify.
   - `evaluate` — the campaign (suite, comparison) is the binary gate
     when there is one (`method=check`). Comparative / inconclusive
     lives in a finding at verify, not in `method`.
   - `incidental` — one observable done-check; usually `check` or
     `manual`; exempt from atomic requirement ids.

6. For each **dependent** task (needs another same-phase task done
   first), create it outside the bundle so the dependency edge can be
   set at creation:

```bash
adaptive-artifacts create --type project:work-item \
  --subject "<task-slug>" \
  --payload '{"title":"<short title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":"R1,R2","decisions":"<decision-a>,<decision-b>"}' \
  --body "## Description

R1: <observable behavior>
R2: <observable behavior>

## Approach

<implementation recipe>" \
  --rel depends_on:<prerequisite-work-item-id>

adaptive-artifacts create --type project:acceptance \
  --subject "<task-slug>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R1"}'
```

7. For a `deliver` or `repair` phase, create the verification task
   last, with one `--rel depends_on:` per other work-item in the
   phase. Give it one thin acceptance per exit criterion (suffixed
   subjects), each naming exactly one requirement id. The
   verification task's acceptances come from the phase exit criteria,
   and one is an integration check through the real entry point. A
   `verify_command` that runs the whole `tests` tree, or
   `tests/test_dashboard_app.py` without a `-k` filter for this
   phase, is not a verification acceptance.

```bash
adaptive-artifacts create --type project:work-item \
  --subject "verify-<phase-slug>" \
  --payload '{"title":"Verify <phase title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":"R1,R2","decisions":"<decision-a>,<decision-b>"}' \
  --body "## Description

Prove the phase exit criteria hold together: run the integration
check through the real entry point, then every other phase check.

## Approach

<implementation recipe>" \
  --rel depends_on:<work-item-id-1> \
  --rel depends_on:<work-item-id-2>

adaptive-artifacts create --type project:acceptance \
  --subject "verify-<phase-slug>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<integration test command>","requirement":"R1"}'

adaptive-artifacts create --type project:acceptance \
  --subject "verify-<phase-slug>-<criterion-suffix>" \
  --payload '{"method":"check","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R2"}'
```

   Add a task that later joins the phase as a `depends_on` edge on the
   verification task (`update --rel`), so the gate still waits for it.

8. **Oracle author** (deliver / repair only; skip for incidental /
   evaluate without tdd oracles). After thin `method=tdd` acceptances
   exist for this phase, dispatch **one** phase-scoped oracle-author
   subagent covering every tdd acceptance that should be oracle-backed.
   Give it only original requirement / specification text (and the
   thin acceptance subjects / requirement ids). Do **not** give it
   work-item Approach, executor briefs, or implementation hints.

   The oracle-author writes failing tests against the current tree and
   returns the node ids and file paths. It does not call
   `adaptive-artifacts` and does not write freeze fields.

   Parent then, for each such acceptance:

   1. Set a provisional `verify_command` from the proposed `test_ids`
      (e.g. `python3 -m pytest <node-id> … -q`) if needed so `aff
      check` can run.
   2. Run `aff check --acceptance <acceptance-id> --cwd <repo-or-worktree>`
      (expect fail).
   3. Freeze **only** when that fail is assertion-level (use
      `affidavit.oracle_red.is_assertion_level_red` on the check-run,
      or equivalent: `result=fail` with assertion failure for a
      failing node — not ImportError / collection ERROR alone).
   4. On assertion-level red, parent writes freeze fields and the
      derived `verify_command`:

```bash
adaptive-artifacts update --type project:acceptance --id <acceptance-id> \
  --expected-revision <revision> \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1","test_ids":"tests/test_<area>.py::test_<case>","oracle_hashes":"tests/test_<area>.py:sha256:<hex>"}'
```

   If the red is not assertion-level, do not freeze — send the
   oracle-author back (still requirement text only) or drop that
   acceptance from the oracle-backed set. Do not open plan review
   while intended oracle-backed tdd acceptances lack freeze fields.

9. Regenerate views:

```bash
adaptive-artifacts handoff --out views/handoff.md
adaptive-artifacts view --id project:plan --out views/plan.md
adaptive-artifacts validate
```

10. Show the user the focus task list, with the verification task and
   the exit criterion each of its acceptances covers. `project:plan`'s rendered view
   doesn't carry `derived.ready`/`wave` (they aren't in the contract's
   `requires_payload` for that role) — query them directly if useful:

```bash
adaptive-artifacts list --type project:work-item \
  --where payload.effort=<effort-slug> --where payload.phase=<current-phase-slug>
```

11. Open the plan review gate, so nothing dispatches before the user
    has seen the tasks (skip for incidental). Do not open the
    plan-review question until those are present: each work-item has
    `## Approach` (the implementation recipe), every task in a wave
    uses the same executor (`inline` or `subagent`), and the phase
    body records size as `one sitting` or `more than one`, the human
    stops, the areas parallel tasks share, and a `## Landing` section.
    Skip the Landing check for incidental work. For deliver / repair,
    also require that each intended oracle-backed tdd acceptance has
    non-empty `test_ids` and `oracle_hashes` from step 8.

```bash
adaptive-artifacts create --type project:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:<current-phase-slug>"}'
```

   Ask the user to approve, change, or send the phase back to
   `discuss`. Change tasks on request. On approval, answer the
   question; only then may `execute-phase` run:

```bash
adaptive-artifacts update --type project:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```
