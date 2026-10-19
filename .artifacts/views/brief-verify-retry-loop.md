# Brief: verify-retry-loop

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### verify-retry-loop
**title**: Verify retry-loop; **phase**: retry-loop; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Prove the phase exit criteria hold together: run the focused retry-loop, dashboard attempt, and skill/contract checks. Do not edit the tree.

## Approach

Run each verify_command for this task's acceptances. Return pass/fail evidence only. No code or skill edits.

## Acceptance Criteria

### verify-retry-loop
**criterion**: Through pytest entry point, retry-loop tests prove redispatch, amendment, attempts, fix_task, budget, and next_plan; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_retry_loop.py -q; state: active

### verify-retry-loop-contract
**criterion**: Skill and contract consistency stay green with optional attempts declared; **method**: check; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q; state: active

### verify-retry-loop-dashboard
**criterion**: Dashboard shows attempt n/budget on retried rows; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k "attempt_row or attempt_budget or attempt_snapshot or attempt_title"; state: active

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
