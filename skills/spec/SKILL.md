---
name: spec
description: >-
  Define a phase's observable behavior and acceptance criteria. Use when
  the user asks to specify a phase or when the workflow routes to spec.
---

# Specify behavior

Requires `canon` and `orchestra` on PATH and a live store. If either is
missing, follow [ensure-store.md](references/ensure-store.md). Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Use
[intent-qa.md](references/intent-qa.md) for discussion.

## Own

- Write one `score:specification` for a full phase.
- State observable behavior and acceptance criteria.
- Preserve constraints, non-goals, invariants, and assumptions.
- Do not write technical design, work-items, acceptance records, or code.

## Phase weight

A phase is `light` when its planned work takes about 4
tasks or fewer, about four hours or less, and fits in one session. When no
option changes the architecture, recommend light. Explain the choice and let
the user override it either way. Record `weight` on the phase. For a full
phase, write a `score:specification` and hand off to design. A light phase
writes no `score:specification` and no `score:design`. Its phase body
has `## Requirements`, `## Proof`, and `## Landing`. Proof uses `demo`,
`commands`, `claims`, or `audit-triage`. Write a decision only when the user
picked between options. Verification, the reviewer, frozen oracles, and
red-first stay the same.

## Steps

1. Resolve the focus and phase from the workflow handoff. Read context:
   the phase, effort brief, milestones, prerequisites, decisions, constraints,
   assessments, and relevant code. Read the phase,
   effort brief, prerequisites, decisions, constraints, and phase assessments.
   Read the brief with:

```bash
canon list --type score:brief --where payload.effort=<focus> --state active --full
```

   When `phase: new`, create the next phase with the highest ordinal plus one.
   Use the phase body shape from `init` step 7. Ask which existing milestone
   it belongs to, or use none. Promote the named idea only when its status is
   `open`:

```bash
canon create --type score:phase \
  --subject "<phase-slug>" \
  --payload '{"title":"<phase title>","ordinal":<next-ordinal>,"effort":"<effort-slug>","milestone":"<milestone-slug>"}' \
  --body-file "<phase-body.md>"

canon list --type composer:idea --subject <idea-subject> --exact-subject --state active --full
canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"promoted","effort":"<effort-slug>","phase":"<phase-slug>"}'
```

Omit `milestone` when the phase is ungrouped.

   Check current clarification markers and blocked questions before discussion.
   Read an existing active specification before you change it.
2. Apply the shared intent Q&A. Ask only about behavior, users, outcomes,
   boundaries, and observable proof. Do not ask the user to choose an
   implementation.
3. Write one atomic requirement per stable `Rn` id. Split a requirement when
   it names more than one observable behavior. Keep existing ids when their
   meaning stays the same.
   Add `[NEEDS CLARIFICATION: <question>]` beside unresolved behavior in a
   specification or design. Resolve every marker before the spec step ends.
   Promote only when the idea's `payload.status` is `open` and the user approves
   the new phase. Preserve persisted assessment values such as `specify`.
4. Present the complete specification. Wait for explicit user approval or
   delegation before you record it. Do not infer consent from a request to
   continue.
5. Create or supersede the current specification. Its subject is the phase
   slug. Its payload `requirements` lists the ids in the body.

```bash
canon create --type score:specification \
  --subject "<phase-slug>" \
  --payload '{"weight":"full","phase":"<phase-slug>","effort":"<effort-slug>","requirements":["R1","R2"]}' \
  --body-file "<specification-body.md>"
```

For a changed specification, use `canon supersede` with the current record id
and expected revision. Do not update a current specification in place.

The body has `## Requirements`, `## Acceptance criteria`, `## Constraints`,
`## Non-goals`, `## Invariants`, and `## Assumptions`. Include every section.
Write `none` when a section has no content. Do not add technical architecture
or implementation choices.

6. Record a workflow review only after explicit user approval or delegation.
   Use the specification record id as the artifact. Use `user-approval` or
   `explicit-delegation` to match what the user said.

```bash
orchestra workflow review <phase-slug> spec \
  --artifact <specification-record-id> \
  --authority user-approval \
  --basis "<user's approval>"
```

Use `explicit-delegation` only when the user delegates the decision. A review
record cannot replace approval.

7. Run `orchestra analyze <phase-slug> --stage spec` and `canon validate`.
   Fix every reported error. Hand off to design only when the workflow
   requests it. A direct spec request ends after the approved specification
   and its review.

## Do not

- Create a design, decision, work-item, acceptance record, or code change
- Turn assumptions into requirements without user agreement
- Bundle multiple outcomes under one requirement id
- Treat silence or a partial answer as approval
- Continue into design or planning after a direct spec request
