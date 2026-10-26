---
name: settle-phase
description: >-
  Settles how a phase will be built before any tasks exist: reads the
  phase and the code it touches, presents two or three approaches with
  trade-offs and a recommendation, and records the user's choice as
  decisions and in the phase body. Structured work also gets one
  specification and one design. Use when engage hands off a new
  deliver, repair, or evaluate phase, or when the user wants to settle
  an approach before plan-phase.
---

# Settle the phase

Requires `canon` and `orchestra` on PATH and a live
orchestra store. If missing,
follow [ensure-store.md](references/ensure-store.md). Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Parent session writes
records.

Do not write work-items, acceptance, or code in this skill. That is
`plan-phase` and `execute-phase`.

## Rules

- One phase per settle. Resolve focus and phase from `engage` or
  the user; if several phases fit, ask.
- **Two-modes rule.** Structured work is a phase that will have a
  specification. Simple work is incidental, or a phase the user is
  leaving on pass/fail. `settle-phase` writes specification and design
  only for structured work. Simple work skips both records.
- Read before proposing: the phase body, live milestones, decisions and
  constraints for this effort, assessments for this phase, and the
  code the phase touches. Read-only search subagents are fine; they
  return text and write nothing.
- Present options, not a plan. Each option: what changes, what it
  costs, what it rules out. Mark one as recommended and say why.
- The user decides. Do not record a choice the user did not make. If
  the user says "your call", record your recommendation and say so in
  the Rationale.
- Skip trivia. A decision is a choice a later reader would otherwise
  re-open. The design names those decisions; it does not replace them.
- Every required section of a specification or design is present. A
  section with nothing to say says `none`.

## Steps

1. Run `orchestra handoff` if the handoff was not injected. Resolve
   **focus**, **kind**, and the **phase** slug. If `engage` handed off
   `phase: new`, create the phase now (`init` step 7 shape) with
   `ordinal` = highest existing ordinal for this effort plus one, and
   a placeholder body. When the effort has milestones, ask which
   milestone the new phase belongs to (or none); set optional payload
   `milestone` to that subject. Create a milestone first only when the
   user wants a new time-bounded group for several phases.
2. Read context: the phase record, milestones for this effort,
   `plan:decision` and `plan:constraint` records with
   `payload.effort` = focus, assessments for this phase, and the code
   paths the phase names or implies.

```bash
canon list --type plan:milestone --where payload.effort=<focus> --state active --full
canon list --type plan:decision --where payload.effort=<focus> --state active --full
canon list --type plan:constraint --where payload.effort=<focus> --state active --full
canon list --type run:assessment --where payload.phase=<phase-slug> --state active --full
canon list --type plan:specification --where payload.phase=<phase-slug> --state active --full
canon list --type plan:design --where payload.phase=<phase-slug> --state active --full
```

3. Present two or three approaches. For each: a short name, what it
   changes, trade-offs, and risks. End with a recommendation. Ask the
   user to choose; use a question tool with one option per approach
   when one is available.
4. Iterate until the user settles each open choice. Narrow follow-up
   questions are fine; do not reopen choices already recorded as
   decisions unless the user asks.
5. Structured work only, before the decision step: one
   `plan:specification` whose subject is the phase slug. Payload
   `requirements` is the stable ids as a JSON array (`["R1","R2"]`). The
   Requirements section uses those ids (`R1: …`). Each id is
   **atomic**: one observable behavior per id. Split compound
   surfaces (commas, "and"-bundled checks, multiple observables under
   one Rn) into separate ids before recording. Refuse compound ids in
   `## Requirements` and in payload `requirements`. Use `weight`
   `light` when the user already fixed the behavior and there is no
   architectural choice; `full` otherwise. When an assessment for this
   phase has `next` `specify`, supersede the specification. Otherwise
   create it when the phase has none.

```bash
canon create --type plan:specification \
  --subject "<phase-slug>" \
  --payload '{"weight":"full","phase":"<phase-slug>","effort":"<effort-slug>","requirements":["R1","R2"]}' \
  --body-file "<specification-body.md>"
```

```bash
canon supersede --type plan:specification --id <specification-id> \
  --expected-revision <revision> \
  --payload '{"weight":"full","phase":"<phase-slug>","effort":"<effort-slug>","requirements":["R1","R2"]}' \
  --body-file "<specification-body.md>"
```

   `<specification-body.md>` has `## Requirements`, `## Acceptance
   criteria`, `## Constraints`, `## Non-goals`, `## Invariants`, and
   `## Assumptions`. Every section is present. A section with nothing
   to say says `none`. Under `## Requirements`, write one line per
   atomic id (`R1: <observable behavior>`). Do not bundle two
   observables under one id. Set payload `weight` to `light` or
   `full` as the rule above says; the sample payload shows `full`.

6. For each settled choice, create a decision. `Counter-argument` is
   the strongest case for the best rejected option, not a strawman:

```bash
canon create --type plan:decision \
  --subject "<decision-topic>" \
  --payload '{"choice":"<adopted>","alternatives":"<rejected options>","phase":"<phase-slug>","effort":"<effort-slug>"}' \
  --body-file "<decision-body.md>"
```

   `<decision-body.md>` has `## Rationale` and `## Counter-argument`
   sections, both non-empty. A decision that overturns an earlier one
   supersedes it instead of adding a second:

```bash
canon supersede --type plan:decision --id <decision-id> \
  --expected-revision <revision> \
  --payload '{"choice":"<adopted>","alternatives":"<rejected options>","phase":"<phase-slug>","effort":"<effort-slug>"}' \
  --body-file "<decision-body.md>"
```

7. Structured work only, after the decisions, so `decisions` names
   them: one `plan:design` with the same subject (the phase slug).
   Payload `decisions` is those decision subjects as a JSON array.
   Required sections hold the architecture, interfaces, invariants,
   assumptions, tradeoffs, and risks. Decisions remain the choices a
   later reader would re-open. When an assessment for this phase has
   `next` `design`, supersede the design and any overturned decision,
   then return to `plan-phase`. Otherwise create the design when the
   phase has none.

```bash
canon create --type plan:design \
  --subject "<phase-slug>" \
  --payload '{"phase":"<phase-slug>","effort":"<effort-slug>","decisions":["<decision-subject>","<decision-subject>"]}' \
  --body-file "<design-body.md>"
```

```bash
canon supersede --type plan:design --id <design-id> \
  --expected-revision <revision> \
  --payload '{"phase":"<phase-slug>","effort":"<effort-slug>","decisions":["<decision-subject>","<decision-subject>"]}' \
  --body-file "<design-body.md>"
```

   `<design-body.md>` has `## Architecture`, `## Interfaces`,
   `## Decisions`, `## Invariants`, `## Assumptions`, `## Tradeoffs`,
   and `## Risks`. Every section is present. A section with nothing
   to say says `none`.

8. Write the chosen approach into the phase body so `plan-phase`
   starts from it. The phase stays `planned`; patch the body without a
   transition:

```bash
canon update --type plan:phase --id <phase-id> \
  --expected-revision <revision> --body-file "<phase-body.md>"
```

   `<phase-body.md>` keeps `## Problem`, `## Approach` (now the chosen
   approach, naming its decisions), and `## Exit criteria`. For
   structured work (and any phase that will use Landing), also include
   a short `## Proof` section: declare `kind` as one of `demo`,
   `commands`, `claims`, `audit-triage`, or `mixed`, plus one sentence
   on what looking means for a human. Default `kind` from the change
   shape when obvious (`claims` for library/evidence work; `demo` only
   when UI/user-visible). `plan-phase` refuses plan review without
   `## Proof` on structured phases.

9. For each question the user could not answer yet and that blocks
   planning, open a continuity-question on the focus:

```bash
canon create --type plan:continuity-question \
  --subject "<effort-slug>" \
  --payload '{"owner":"<who answers>","blocking":true,"scope":"<what it blocks>"}'
```

   When the user answers it, clear it at the event (kinds-and-focus,
   Needs-you clears):

```bash
canon update --type plan:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>
```

10. Run `canon validate`. Show the user
    the specification, the design, the decisions, and the phase
    approach. Next is `plan-phase` for this phase, including after a
    `next` `design` supersede.

## Do not

- Write work-items, acceptance, or code
- Write a specification or a design for simple work
- Record a choice the user did not make
- Promote the phase to `in_progress` (`plan-phase` does that)
- Settle another effort's phases
- Let subagents write records
