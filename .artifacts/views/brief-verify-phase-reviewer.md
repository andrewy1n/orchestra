# Brief: verify-phase-reviewer

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### verify-phase-reviewer
**title**: Verify phase-end independent reviewer; **phase**: phase-reviewer; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Prove the phase exit criteria hold together: run the phase-reviewer tests through pytest (real entry point), the status-tabs fixture, and skill/contract consistency. Do not edit the tree.

## Approach

Run each verify_command for this task's acceptances. Return pass/fail evidence only. No code or skill edits.

## Acceptance Criteria

### verify-phase-reviewer
**criterion**: Through pytest entry point, phase-reviewer tests prove brief limits, parent review check-run/findings, fix routing, one re-run, gate, and integration-report from reviewer output; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q; state: active

### verify-phase-reviewer-agent
**criterion**: Reviewer agent exists with restricted tools and sync-plugin installs it; execute-phase documents phase-end invocation after verification; **method**: check; **effort**: workflow-loop; **verify_command**: test -f agents/se-reviewer.md && grep -qiE "no Write|without Write" agents/se-reviewer.md && grep -q agents/ scripts/sync-plugin.sh && grep -qiE "reviewer|se-reviewer" skills/execute-phase/SKILL.md; state: active

### verify-phase-reviewer-contract
**criterion**: Skill and contract consistency stay green with review check-run and phase-end reviewer writes; **method**: check; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py tests/test_contract_self_consistency.py -q; state: active

### verify-phase-reviewer-fixture
**criterion**: status-tabs fixture returns NEEDS_WORK / spec-gap; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs; state: active

### verify-phase-reviewer-gate
**criterion**: Phase gate requires passing review at head before merge; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate; state: active

## Findings

_None._

## Constraints

_None._

## Position

### phase-reviewer
**position**: executing wave 3: verify-phase-reviewer; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop done; next up: phase-reviewer; **scope**: effort; state: active

## Unapplied Amendments

_None._
