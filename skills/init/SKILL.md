---
name: init
description: >-
  Adopts the current git repo into the orchestra store: live goal,
  and a score:phase record for every phase you can currently name. Does not write work-items or a plan
  document.
  Specification and design are written by `settle-phase`, not `init`. Use
  when starting this workflow on an existing or empty project, when
  adding a new effort subject, or when handoff has no goal or
  position.
---

# Adopt this repo

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md) in the **current work repo**.
Follow [kinds-and-focus.md](references/kinds-and-focus.md). Do not copy this
plugin into the project.

Skip this skill for incidental work that fits in the current chat.
If `engage` already named a new focus, use that subject here.
If the user already has this focus's tasks, use `plan-phase`.

## Rules

- Records are the authority. Views are derived. Do not write a plan
  or roadmap file as authority.
- Specification and design are written by `settle-phase`, not `init`.
- Interview for orientation, not an executable multi-phase plan. A
  phase record's body must have real content in every required
  section, but "not yet scoped" is real content for a phase that
  hasn't started — do not fabricate success criteria or dependencies
  for it.
- Every phase you can currently name gets a `score:phase` record,
  `planned`, ordinal in sequence. None of them start `in_progress`
  here — `plan-phase` promotes the one it's about to materialize work
  for. Incidental work gets **no** phase record at all.
- Each exit criterion states how it is verified: the command, test,
  or observation that proves it. A later phase may say "decide at
  plan-phase" for the detail, but it still names the verification
  gate: every acceptance passes and an integration check through the
  real entry point passes. `plan-phase` turns each criterion into an
  acceptance on the phase's verification task.
- When the phases of a multi-phase effort only prove themselves
  together (a library plus its caller, a view plus its renderer),
  propose a final end-to-end verification phase that runs the whole
  flow through the real entry point.
- Existing docs (README, git log, other project docs) are input.
  Confirm with the user before writing records. Do not ingest them
  as replicas.
- Current-claims (`score:effort`, `score:position`, `decision`,
  `constraint`) change via `supersede` (new id), never `update` to
  `superseded`, never payload-only `update`. `score:phase` is a
  different trait (staged lifecycle) — it changes via `update
  --transition`, never `supersede`.
- Parent writes records. Do not spawn subagents here.
- Several live goals may exist. A new effort is a new `subject`, and
  needs a reason: no live goal covers this area. Never supersede
  another subject's goal or position.

## Steps

1. Follow ensure-store. If cwd is not git, stop after saying so.
2. Run `orchestra handoff` if the handoff was not injected.
3. Resolve **focus** (effort slug). If live goals already exist, show
   them. Keep them unless the user is replacing **that** subject.
   If a live goal covers the same area, the work is a new phase there
   (`plan-phase`), not a new subject. Never rewrite a different goal.
   If a closed goal has this subject or covers the area, reopen it
   (kinds-and-focus) instead of creating a new goal.
4. Read cheap local evidence only: README, recent `git log`, existing
   docs. Treat them as proposals, not authority.
5. Propose, then confirm (do not invent a product plan):
   - **focus** — effort slug
   - **kind** — `deliver` | `repair` | `evaluate` | `incidental`
   - **goal** — live outcome of this effort
   - **milestones** — optional ordered list of `{slug, title}` when
     the effort is long enough to group phases (time-bounded
     outcomes). Omit when every phase stands alone.
   - **phases** — ordered list of `{slug, title, milestone?}`,
     current phase first; empty for incidental. `milestone` is a
     milestone slug from the list above, or omit. Add a final
     end-to-end verification phase when the pieces only prove
     themselves together.
   - **blocking unknown** — only if dispatch or resume cannot proceed
   - **durable decisions / constraints** — already-made choices or
     confirmed non-negotiables; skip trivia
   Ask only what is still missing after the proposal. If the user
   starts listing tasks or acceptance, stop and point to `plan-phase`.
6. Same `subject` for goal and position (the focus slug). Create
   `score:effort` for that subject only:

```bash
canon create --type score:effort \
  --subject "<effort-slug>" \
  --payload '{"goal":"<live outcome>","kind":"deliver"}'
```

   `kind` is the effort kind from step 5.

   When `kind` is `deliver`, also create the effort's `score:brief`
   with the effort slug as subject:

```bash
canon create --type score:brief \
  --subject "<effort-slug>" \
  --payload '{"effort":"<effort-slug>"}' \
  --body-file "<brief-body.md>"
```

   `<brief-body.md>` has these headings; every section needs
   non-empty text:

```markdown
## Problem
## Users
## Success measure
## Non-goals
```

   Efforts of kind `repair`, `evaluate`, or `incidental` get no
   `score:brief`.

   When the routing line from `engage` names an area (not `none`),
   run `orchestra place <effort-slug> <area>`. Skip otherwise.

7. For each milestone in step 5 (skip when none), `create --type
   score:milestone`, `ordinal` starting at 1:

```bash
canon create --type score:milestone \
  --subject "<milestone-slug>" \
  --payload '{"title":"<milestone title>","ordinal":1,"effort":"<effort-slug>"}' \
  --body-file "<milestone-body.md>"
```

   `<milestone-body.md>` has `## Outcome` and `## Exit criteria`;
   every section needs non-empty text.

   Then for each phase in step 5's list (skip entirely for
   incidental), `create --type score:phase`, `ordinal` starting at
   1 across the effort (not per milestone). Include optional
   `milestone` when the phase belongs to one. Give a later phase's
   Approach/Exit-criteria a short honest placeholder ("decide at
   plan-phase") rather than guessing detail — a plan-phase run for
   that phase will overwrite it. Use `--body-file` once the text is
   more than a couple of lines:

```bash
canon create --type score:phase \
  --subject "<phase-slug>" \
  --payload '{"title":"<phase title>","ordinal":1,"effort":"<effort-slug>","milestone":"<milestone-slug>"}' \
  --body-file "<phase-body.md>"
```

   Omit `milestone` from the payload when the phase is ungrouped.
   `<phase-body.md>` has `## Problem`, `## Approach`, `## Exit
   criteria` headings; every section needs non-empty text or the
   record is rejected. Write each exit criterion with how it is
   verified, for example "`<cmd>` renders X against a seeded store
   (integration test)", not only the outcome.

8. Create `score:position` on the same subject as step 6.
   `scope` is a **stable** value for this subject (e.g. "effort or
   repo") — never the current phase slug. Keep it identical across
   `supersede` calls. `phase` is
   a required payload reference to a real `score:phase` subject —
   set it to the first phase from step 5's list (the one step 7 just
   created at `ordinal: 1`). That is a pointer for this record, not an
   authority: which phase is actually current is still derived by
   querying `score:phase` for this effort with
   `lifecycle_state=in_progress` (nothing is `in_progress` yet this
   early — `plan-phase` promotes it) — never read off this field.
   `position` is a short "where we are now" narrative (may name the
   current phase in prose) — do not restate the phase list, that's
   what the `score:phase` records are for. If a position already
   exists **for this subject**, supersede it with `--expected-revision`,
   keeping `scope` identical to the predecessor's and `phase` current.
   Do not touch other subjects.

```bash
canon create --type score:position \
  --subject "<effort-slug>" \
  --payload '{"position":"<short now-statement>","scope":"<effort or repo>","effort":"<effort-slug>","phase":"<first-phase-slug>"}'
```

   When the routing line from `engage` carries `idea: <subject>` (not
   `none`), read that idea and supersede it to `promoted` with this
   effort:
   Promote only when the idea's `payload.status` is `open`; otherwise
   skip the promotion and say so.

```bash
canon list --type composer:idea --subject <idea-subject> --exact-subject --state active --full

canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"promoted","effort":"<effort-slug>"}'
```

   Skip when the routing line has `idea: none`.

9. For each confirmed durable choice among alternatives,
   `create --type score:decision` with `choice`, `alternatives`,
   `phase`, `effort` payload and a body with `## Rationale` and
   `## Counter-argument` sections (both required, both non-empty —
   state the real counter-argument, not a strawman):

```bash
canon create --type score:decision \
  --subject "<decision-topic>" \
  --payload '{"choice":"<adopted>","alternatives":"<a, b>","phase":"<phase-slug>","effort":"<effort-slug>"}' \
  --body-file "<decision-body.md>"
```

   For a confirmed constraint that is **not** a choice — no real
   alternative existed — use `score:constraint` instead, with a
   `## Basis` section:

```bash
canon create --type score:constraint \
  --subject "<constraint-slug>" \
  --payload '{"statement":"<the constraint>","applies_to":"<what it binds>","effort":"<effort-slug>"}' \
  --body "## Basis

<why this is confirmed, not a choice>"
```

10. For each confirmed blocker: `create --type score:continuity-question`
    with `subject` = focus, `owner`, `blocking` true/false, `scope`.
11. Do **not** create `work-item`, `acceptance`, `specification`, or
    `design`. Specification and design are written by `settle-phase`,
    not `init`.
12. Validate:

```bash
canon validate
```

13. Show the user (`orchestra view plan --effort <focus>`): focus, kind, goal, milestones (if any), phase list
    (slug + title + lifecycle + milestone), any blockers. Next is
    `settle-phase` then `plan-phase` when they want the current phase
    settled and tasked.

## Do not

- Materialize future phases as work-items or full plans — a
  placeholder Problem/Approach/Exit-criteria body is enough
- Write `score:specification` or `score:design` — `settle-phase`
  writes those
- Write a roadmap document
- Run research or planner subagents
- Supersede another subject's live goal to "make room"
- Transition any phase to `in_progress` here — that's `plan-phase`'s job
