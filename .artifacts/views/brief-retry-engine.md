# Brief: retry-engine

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### retry-engine
**title**: Contract attempts + retry skills and tests; **phase**: retry-loop; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Declare optional work-item `attempts`, teach execute-phase/plan-phase/verify-work the retry loop (re-dispatch, amendments, fix tasks, budget, next: plan), and prove it with focused tests.

## Approach

1. Add optional integer `attempts` on `project:work-item` in `contract/project-design.json`; sync `.artifacts/project-design.json` and `adaptive-artifacts resolve` if the dogfood store contract must match.
2. In `skills/execute-phase/SKILL.md`, before planned ready selection: select retryable `in_progress` tasks; write assignment-amendment quoting failure evidence; increment `attempts`; re-dispatch same executor; enforce per-task and per-phase fix-task budgets (defaults + run-fact overrides); on exhaustion create blocking continuity-question `scope: retry:<task-slug>` and `needs: human` finding; on closing-verification fail create fix work-item + `depends_on` (never reopen `done`).
3. In `skills/plan-phase/SKILL.md`, handle assessment `next: plan` by adding missing tasks and re-opening plan review.
4. In `skills/verify-work/SKILL.md`, note that parent will re-dispatch or create fix tasks; do not change evidence-escalation routing.
5. Add `tests/test_retry_loop.py` for redispatch/amendment/attempts, fix_task/depends_on/no_reopen, budget, and next_plan. Keep skill-contract consistency green.

## Acceptance Criteria

### retry-engine
**criterion**: test_retry_loop covers redispatch, amendment, attempts, fix_task/depends_on/no_reopen, budget exhaustion, and next_plan; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_retry_loop.py -q; state: active

### retry-engine-contract
**criterion**: Optional attempts is on work-item; skill invocations stay contract-legal; consistency tests green; **method**: check; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q; state: active

## Findings

_None._

## Constraints

_None._

## Position

### retry-loop
**position**: plan approved; executing wave 1; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop through dashboard-approvals discussed; next plan-phase on retry-loop; **scope**: effort; state: active

## Unapplied Amendments

_None._
