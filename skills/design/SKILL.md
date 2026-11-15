---
name: design
description: >-
  Choose a viable technical approach for an approved phase specification.
  Use when the user asks for design or the workflow routes to design.
---

# Design the approach

Requires `canon` and `orchestra` on PATH. Run `orchestra workflow brief <phase> design` for your instructions, or use the `brief` that `orchestra workflow next` returns. If `orchestra` is not on PATH, stop and tell the user to install orchestra.

## Own

- Write one `score:design` against the active approved specification.
- Compare only approaches that satisfy the full behavioral contract.
- Record decisions only when the user chooses between real alternatives.
- Do not write work-items, acceptance records, or code.

For a light phase, skip specification and design records. Record a decision
only when the user chooses between approaches. Do not record a recommendation
as a decision.

## Do not

- Design against a missing or stale specification
- Offer an approach that fails any agreed requirement
- Create work-items, acceptance records, or code changes
- Treat silence or a partial answer as approval
- Turn a recommendation into a recorded decision without user approval
- Continue into task planning after a direct design request
