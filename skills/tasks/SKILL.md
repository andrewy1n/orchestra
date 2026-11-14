---
name: tasks
description: >-
  Turn the approved phase contract into requirement-linked work-items and
  acceptance records. Use when the workflow routes to tasks.
---

# Plan tasks

Requires `canon` and `orchestra` on PATH. Run `orchestra workflow brief <phase> tasks` for your instructions, or use the `brief` that `orchestra workflow next` returns. If `orchestra` is not on PATH, stop and tell the user to install orchestra.

## Own

- Materialize work-items and acceptance records for the current phase.
- Keep task scope limited to the selected phase.
- End with a closing verification task for `deliver` and `repair` phases.
- Stop after planning and its existing review gate.

## Do not

- Write technical design, code, execution reports, check-runs, or assessments
- Plan future phases or other efforts
- Guess dependencies from phase ordinals
- Mark work-items ready or assign wave numbers by hand
- Let a planning conversation replace the existing review gate
