---
name: tasks
description: >-
  Turn the approved phase contract into requirement-linked work-items and
  acceptance records. Use when the workflow routes to tasks.
---

# Plan tasks

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md),
[kinds-and-focus.md](references/kinds-and-focus.md), and
[record-mechanics.md](references/record-mechanics.md). Follow
[task-shapes.md](references/task-shapes.md) and
[oracle-author.md](references/oracle-author.md) when planning TDD work.
Follow [planning-mechanics.md](references/planning-mechanics.md) for the
complete plan review and record rules.

## Own

- Materialize work-items and acceptance records for the current phase.
- Keep task scope limited to the selected phase.
- End with a closing verification task for `deliver` and `repair` phases.
- Stop after planning and its existing review gate.

## Steps

1. Resolve the focus and phase from the handoff. Read the active specification
   or the phase `## Requirements`, current spec/design reviews, decisions,
   constraints, assessments, and `orchestra view plan`. Refuse to plan against
   a stale or unapproved contract.
2. Use stable atomic requirement ids. Map every `deliver` or `repair`
   work-item to its requirement ids. Pin current input reviews in its
   `source_reviews` array. Give each acceptance one requirement, unless a
   single check proves several requirements together.
3. Split independent work first. Add `depends_on` only for real ordering or
   data dependencies. Make the closing verification task depend on every
   other phase task.
4. Give each work-item `## Description`, `## Approach`, one executor type,
   `size` (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock, not padded).
   `executor` is `inline` or `subagent`. Missing means `subagent`. Every
   task in one wave uses the same executor.
   Guidance: XS 2–5, S 5–10, M 8–15, L 15–25, XL 25–40.
   Phase body records session shape (`one sitting` | `more than one`), human
   stops, and shared areas. Use focused tasks and reserve whole-phase verification
   for the final task.
5. For oracle-backed TDD, freeze `test_ids` and `oracle_hashes` in the initial
   acceptance create. Run the oracle author before the batch. Freeze only
   after assertion-level red.
6. Draft records, then apply all phase work-items and acceptances through one
   ordered NDJSON batch. Put prerequisites first and acceptances after their
   work-item. Do not create records one by one.
7. Run and inspect this command:

```bash
orchestra analyze <phase-slug> --stage plan
```

   Refuse plan review if this command exits 1. Fix each finding. Follow the phase
   autonomy and plan review gate. Do not start execution here.

For `next: plan`, add only tasks that cover the missing requirements. Review
the delta through the plan review gate.

No Landing → not ready for plan review. Incidental has no Landing.
Open the plan review gate (skip incidental). Do not open until task recipes,
wave executor choices, phase run facts, proof, Landing, and frozen oracle
fields pass review. Skip this gate at
`auto-plan` and `auto-phases`.

The phase body records its `## Proof` kind as `demo`, `commands`, `claims`,
`audit-triage`, or `mixed`. A light phase may use one acceptance with a
`requirements` array when one check proves each listed requirement.

```bash
canon create --type score:continuity-question \
  --subject "<focus>" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:<current-phase-slug>"}' \
  --body "Review the phase plan. Approve, change, or send it back to spec."
```

After approval, answer the plan-review question. Start execution only after
the answer clears the blocking question.

Landing names branch, worktree, base and repo only. `orchestra.toml` `[land]`
and `[suite]` configure them.

## Do not

- Write technical design, code, execution reports, check-runs, or assessments
- Plan future phases or other efforts
- Guess dependencies from phase ordinals
- Mark work-items ready or assign wave numbers by hand
- Let a planning conversation replace the existing review gate
