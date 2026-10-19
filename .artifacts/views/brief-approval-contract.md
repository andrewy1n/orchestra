# Brief: approval-contract

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### approval-contract
**title**: Optional note fields on gate records; **phase**: dashboard-approvals; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Add optional payload fields the dashboard needs to record approval notes without inventing out-of-contract keys.

## Approach

1. In `contract/project-design.json`, add optional `answer` on `continuity-question`, `signed_note` on `check-run`, and `resolution_note` on `finding` (names may match design equivalents if already present).
2. Mirror into `.artifacts/project-design.json` if the store design is the working copy, then `adaptive-artifacts resolve`.
3. Extend contract/self-consistency or skill-contract tests so optional fields are accepted and skills mentioning them stay legal.
4. Do not change dashboard UX in this task.

## Acceptance Criteria

### approval-contract
**criterion**: Bundled contract resolves with optional answer, signed_note, and resolution_note on the gate types; skill↔contract consistency and contract self-consistency tests pass; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_contract_self_consistency.py tests/test_skill_contract_consistency.py -q -k 'approval or continuity or signed_note or resolution_note or optional_payload or contract'; state: active

## Findings

_None._

## Constraints

_None._

## Position

### dashboard-approvals
**position**: dashboard-approvals planned; waiting on plan review; **scope**: phase; state: active

### phase-reviewer
**position**: phase-reviewer done; next up: tiered-verification; **scope**: phase; state: active

### workflow-loop
**position**: tiered-verification done; next up: dashboard-approvals; **scope**: effort; state: active

## Unapplied Amendments

_None._
