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

- Write one `score:specification` for the selected phase.
- State observable behavior and acceptance criteria.
- Preserve constraints, non-goals, invariants, and assumptions.
- Do not write technical design, work-items, acceptance records, or code.

## Steps

1. Resolve the focus and phase from the workflow handoff. Read the phase,
   effort brief, prerequisites, decisions, constraints, and phase assessments.
   Read an existing active specification before you change it.
2. Apply the shared intent Q&A. Ask only about behavior, users, outcomes,
   boundaries, and observable proof. Do not ask the user to choose an
   implementation.
3. Write one atomic requirement per stable `Rn` id. Split a requirement when
   it names more than one observable behavior. Keep existing ids when their
   meaning stays the same.
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
