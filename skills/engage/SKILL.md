---
name: engage
description: >-
  Classifies a software-engineering ask as deliver, repair, evaluate,
  or incidental, names the focus subject, and hands off to init,
  settle-phase, plan-phase, execute-phase, or verify-work. The ask may
  name a triaged `composer:idea` subject. Use when the user has work
  but has not named a phase skill, when the work is a bug, one-off,
  integration test, or metric comparison.
---

# Engage

Thin router. Classify, name focus, stop. Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Follow
[ensure-store.md](references/ensure-store.md) if a store will be needed.

Do not plan, implement, or verify in this skill.

## Steps

1. If the handoff was not injected and `.canon/` exists, run
   `orchestra handoff`. Read it. List live goal subjects with their
   goal text and phases.
2. Classify the ask (first match):

   | The text is about… | kind |
   |---|---|
   | Something broken, a bug, a repro, a crash | `repair` |
   | The job is a campaign, integration suite, bake-off, or metric comparison | `evaluate` |
   | Already-planned work, “run the phase”, “continue tasks” | keep existing kind; go to step 7 |
   | “Show this is done”, tests were run | keep existing kind; go to step 7 |
   | A small chore, typo, or unrelated change | `incidental` |
   | A specified feature, phase, or known change | `deliver` |

   If two rows fit, ask the user to pick.
3. Name **focus** (effort slug). When the ask names an open
   `composer:idea`, skip this step and use step 4. An effort is a
   product area or objective; one ask is usually one phase inside it.
   Compare the ask with each live goal's text:

   - A live goal covers the same area → reuse its subject, even when
     the kind differs (`kind` lives on each work-item). If no phase
     covers the ask, it becomes a **new phase** of that effort.
   - Several goals fit, or the fit is unclear → list the candidates
     and ask the user.
   - A **closed** goal covers the area → reopen it (kinds-and-focus,
     Closing and reopening) and reuse its subject; the ask is a new
     phase there.
   - No live or closed goal covers the area → pick a new slug
     (`login-500`, `p95-compare`).
   - `incidental` with records → always a new slug (see
     kinds-and-focus).

   Do not rename another effort’s subject to steal its goal.

   After focus is named, list open **human-dismissible** Needs-you
   items for that effort (open `continuity-question`s, `finding`s with
   `needs` `human`, unsigned manual `check-run`s with empty
   `signed_by`). Read them from the `## <focus>` handoff section
   (Needs Human, Unsigned Manual Check, and open questions). Remind
   yourself to clear each one when the user settles it (kinds-and-focus,
   Needs-you clears). Do not refuse to route solely because those items
   are open — list and remind, then continue routing.

   Also list open `composer:idea` records for this focus
   (`payload.status=open`, `payload.effort` set). Show them; do not
   treat them as Needs-you.

```bash
canon list --type composer:idea \
  --where payload.effort=<focus> --where payload.status=open --state active
```

   - **Park** — user defers work for later: create an idea (parent
     writer) with `effort`, `status` `open`, and optional `source`.
   - **Start** — user starts a parked item: treat the ask as naming
     that idea's subject; go to step 4. Promotion to `promoted`
     happens in `init` or `settle-phase`, not here.
   - **Dismiss** — user drops a parked item: supersede to `dismissed`.

```bash
canon create --type composer:idea \
  --subject "<item-slug>" \
  --payload '{"effort":"<effort-slug>","status":"open","source":"<optional>"}' \
  --body "<parked description>"

canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"dismissed","effort":"<effort-slug>"}'
```

4. Idea input. When the ask names the subject of an open
   `composer:idea`, or the user asks to start from an idea, use this
   path. Use the idea for **focus** instead of step 3.

   - When no idea subject is named, run `orchestra view roadmap`.
     List the open ideas grouped by area. Ask the user to pick one.
   - Read the idea:

```bash
canon list --type composer:idea \
  --subject <idea-subject> --exact-subject --state active --full
```

   - When `payload.status` is not `open`, say so and stop.
   - When the idea has `payload.effort`, set **focus** to that
     effort. The ask is a new phase of that effort; hand off with
     `settle-phase` and `phase: new` when records apply.
   - When the idea has no effort, route to `init` for a new effort.
     Propose a focus slug from the idea subject. Ask the user to
     confirm.
   - When the idea's effort is closed, reopen it first
     (kinds-and-focus, Closing and reopening).
   - Set `idea: <idea-subject>` on the routing line.
   - The idea path always routes through `settle-phase` with
     `phase: new`, or through `init`. Do not skip them and do not send
     the idea to `plan-phase` or the incidental shortcut, because
     `settle-phase` and `init` promote the idea.
   - Engage writes nothing on this path. The idea stays `open` until
     `init` or `settle-phase` promotes it. When the user stops before
     an effort or phase exists, the idea stays `open`.

   When this step does not apply, set `idea` to `none` on the routing
   line.

5. Area. For a **new** effort, ask the user which area it belongs to.
   Once the effort exists (after `init`), run
   `orchestra place <effort> <area>`. Skip this step for an existing
   effort.
6. Records?

   - `incidental` + fits this chat + not interrupting another live
     phase → **no records**. Tell the user to do it in this chat.
     Stop.
   - `incidental` + may span chats or interrupts a live phase → records
     on the **new** focus subject. Next: `plan-phase`.
   - `deliver` / `repair` / `evaluate` and no store or no goal for
     this focus → `init` (new subject), then `settle-phase`, then
     `plan-phase`.
   - Existing effort and no phase covers the ask → `settle-phase`
     with `phase: new`, then `plan-phase`.
   - Tasks for this focus already exist → `execute-phase` or
     `verify-work` if they only need a done-check.
   - Otherwise → `settle-phase` if the phase has no decisions yet,
     else `plan-phase`.

   Skip `settle-phase` (go straight to `plan-phase`) when the user
   already fixed the approach in this ask, or for `incidental`.
7. Show the routing line, then follow that skill with focus and kind
   in context:

   ```
   kind: <kind>
   focus: <effort-slug> (existing | new)
   phase: <phase-slug> | new | none
   idea: <subject> | none
   records: yes | no
   next: <skill or "this chat">
   ```

## Do not

- Spawn subagents
- Supersede another subject’s goal or position
- Write work-items here
- Promote an idea from engage
- Add a fifth kind
