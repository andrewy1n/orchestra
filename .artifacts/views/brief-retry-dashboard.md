# Brief: retry-dashboard

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### retry-dashboard
**title**: Show attempt n/budget on retried rows; **phase**: retry-loop; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Dashboard task rows with attempts > 0 show attempt n/budget using the effective per-task budget (default 2 or run-fact override).

## Approach

1. Extend dashboard model TaskRow (or equivalent) to expose attempts and effective budget from work-item payload / documented defaults.
2. Render `attempt n/budget` on retried rows in the effort/phase task UI.
3. Add model and app pilots filtered with `-k attempt` (or a dedicated marker name used in verify_command). Do not edit skills/ or contract/.

## Acceptance Criteria

### retry-dashboard
**criterion**: Retried task rows show attempt n/budget; model/app tests with -k attempt pass; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_app.py -q -k attempt; state: active

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
