---
name: design
description: >-
  Choose a viable technical approach for an approved phase specification.
  Use when the user asks for design or the workflow routes to design.
---

# Design the approach

Requires `canon` and `orchestra` on PATH and a live store. If either is
missing, follow [ensure-store.md](references/ensure-store.md). Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Use
[intent-qa.md](references/intent-qa.md) for discussion.

## Own

- Write one `score:design` against the active approved specification.
- Compare only approaches that satisfy the full behavioral contract.
- Record decisions only when the user chooses between real alternatives.
- Do not write work-items, acceptance records, or code.

## Steps

1. Resolve the focus and phase from the workflow handoff. Read the active
   specification, its review, the phase, decisions, constraints, assessments,
   and relevant code. Refuse to design when no current approved specification
   exists. Route back to spec when the contract is missing or stale.
2. Research relevant code and current technical facts before asking the user
   about preferences. Apply the shared intent Q&A. Ask about only choices that
   change architecture, interfaces, recovery, cost, or risk.
3. Present two or three viable approaches when real alternatives exist. Offer
   only approaches that satisfy the specification. Explain their changes,
   trade-offs, and risks. Recommend one approach and explain why. Do not
   present invalid or infeasible choices as options.
4. Walk through normal operation, recovery, upstream changes, and verification
   when those cases affect the choice. Skip a walkthrough when it adds no
   decision-relevant information.
5. Present the complete design. Wait for explicit user approval or delegation
   before you record it. Do not infer consent from a request to continue.
6. Record each settled choice as a `score:decision`. Give each decision a
   stable subject. Include `## Rationale` and `## Counter-argument`; both
   sections must be non-empty. The counter-argument gives the strongest case
   for the best rejected option.

```bash
canon create --type score:decision \
  --subject "<decision-topic>" \
  --payload '{"choice":"<adopted>","alternatives":"<rejected options>","phase":"<phase-slug>","effort":"<effort-slug>"}' \
  --body-file "<decision-body.md>"
```

7. Create or supersede the phase `score:design`. Its payload `decisions` lists
   the decision subjects. Its body has `## Architecture`, `## Interfaces`,
   `## Decisions`, `## Invariants`, `## Assumptions`, `## Tradeoffs`, and
   `## Risks`. Include every section. Write `none` when a section has no
   content. Keep a light phase compact.

```bash
canon create --type score:design \
  --subject "<phase-slug>" \
  --payload '{"phase":"<phase-slug>","effort":"<effort-slug>","decisions":["<decision-topic>"]}' \
  --body-file "<design-body.md>"
```

For a changed design, use `canon supersede` with the current record id and
expected revision. Do not update a current design in place.

8. Record a workflow review only after explicit user approval or delegation.
   Use the design record id as the artifact. Match `authority` to the user's
   action. A review record cannot replace approval.

```bash
orchestra workflow review <phase-slug> design \
  --artifact <design-record-id> \
  --authority user-approval \
  --basis "<user's approval>"
```

9. Run `orchestra analyze <phase-slug> --stage design` and `canon validate`.
   Fix every reported error. A direct design request ends after the approved
   design and its review. Planning remains a separate workflow step.

## Do not

- Design against a missing or stale specification
- Offer an approach that fails any agreed requirement
- Create work-items, acceptance records, or code changes
- Treat silence or a partial answer as approval
- Turn a recommendation into a recorded decision without user approval
- Continue into task planning after a direct design request
