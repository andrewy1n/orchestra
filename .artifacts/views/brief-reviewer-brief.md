# Brief: reviewer-brief

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### reviewer-brief
**title**: Build restricted reviewer brief; **phase**: phase-reviewer; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

A brief builder composes only work-item titles/descriptions/Approach goals, acceptances, structured requirements/invariants, and phase diff/tree pointers — never execution-reports, check-runs, assessments, or assignment notes. A test proves those excluded kinds are absent from the brief.

## Approach

1. Add `se_workflow/reviewer.py` (or equivalent) that builds the reviewer brief from store-derived task/spec text plus `git diff <base>..<phase-head>`.
2. Reject or strip execution-report, check-run, assessment, and assignment content if present in inputs.
3. Add `tests/test_phase_reviewer.py` (or focused module) asserting the brief excludes those kinds. Do not edit execute-phase skill yet.

## Acceptance Criteria

### reviewer-brief
**criterion**: A test asserts the reviewer brief excludes execution-report, check-run, and assessment content; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k brief; state: active

## Findings

_None._

## Constraints

_None._

## Position

### phase-reviewer
**position**: executing wave 1: se-reviewer-agent + reviewer-brief; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop done; next up: phase-reviewer; **scope**: effort; state: active

## Unapplied Amendments

_None._
