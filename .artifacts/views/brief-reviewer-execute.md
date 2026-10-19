# Brief: reviewer-execute

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### reviewer-execute
**title**: Wire phase-end reviewer into execute-phase; **phase**: phase-reviewer; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

After the closing verification task succeeds, execute-phase dispatches the read-only reviewer with the restricted brief, parent-records the review check-run and findings, routes fixable NEEDS_WORK through retry-loop fix tasks with one re-run, writes the integration-report from reviewer output, and requires a passing review at phase head before merge.

## Approach

1. In `skills/execute-phase/SKILL.md`, change phase-end order to: last implementation wave → closing verification → reviewer → integration-report from reviewer `integration` section → phase gate (include passing `method: review` check-run at head) → Landing merge. Remove or relocate the pre-verification integration-report write for this path so the report content comes from the reviewer.
2. Parent only: create `project:check-run` with `method: review`, `evidence_kind: review`, `revision` = phase head, `result` from verdict; one `project:finding` per NEEDS_WORK (`needs: none` when a fix task is created, `needs: human` for judgment).
3. Reuse retry-loop fix-task + budget for fixable kinds; re-run reviewer once after fixes; budget exhaustion escalates (continuity-question / needs human). Never reopen `done`.
4. Gate: no merge without a passing review check-run at the phase-head SHA.
5. Extend `tests/test_phase_reviewer.py` (and skill-contract consistency) for parent writes, fix routing, one re-run, gate, and integration-report sourcing. Do not implement the status-tabs fixture here.

## Acceptance Criteria

### reviewer-execute
**criterion**: execute-phase invokes the reviewer after closing verification and before merge; parent records method:review / evidence_kind:review check-run at head and findings for NEEDS_WORK; reviewer writes no store records; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "execute or parent_write or review_check"; state: active

### reviewer-execute-fix
**criterion**: Fixable NEEDS_WORK creates fix work-items under the retry budget; reviewer re-runs once after fixes; exhausted budget escalates without reopening done tasks; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k "fix_task or rerun or budget"; state: active

### reviewer-execute-gate
**criterion**: Phase gate requires a passing review check-run at the phase head SHA before merge; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k gate; state: active

### reviewer-execute-integration
**criterion**: Integration-report body is filled from the reviewer integration section; skill/contract consistency stays green; **method**: check; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py tests/test_skill_contract_consistency.py -q -k "integration or test_skill_contract"; state: active

## Findings

_None._

## Constraints

_None._

## Position

### phase-reviewer
**position**: executing wave 2: reviewer-execute; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop done; next up: phase-reviewer; **scope**: effort; state: active

## Unapplied Amendments

_None._
