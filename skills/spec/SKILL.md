---
name: spec
description: >-
  Define a phase's observable behavior and acceptance criteria. Use when
  the user asks to specify a phase or when the workflow routes to spec.
---

# Specify behavior

Requires `canon` and `orchestra` on PATH. Run `orchestra workflow brief <phase> spec` for your instructions, or use the `brief` that `orchestra workflow next` returns. If `orchestra` is not on PATH, stop and tell the user to install orchestra.

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
picked between options. Verification, the reviewer, selected frozen oracles,
and TDD red-first stay the same. Follow the verification policy in the brief.

## Do not

- Create a design, decision, work-item, acceptance record, or code change
- Turn assumptions into requirements without user agreement
- Bundle multiple outcomes under one requirement id
- Treat silence or a partial answer as approval
- Continue into design or planning after a direct spec request
