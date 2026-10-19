# Brief: status-tabs-fixture

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### status-tabs-fixture
**title**: status-tabs NEEDS_WORK / spec-gap fixture; **phase**: phase-reviewer; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

A regression fixture replays the status-tabs dogfood case (description lists more UI than acceptance/diff deliver) and the reviewer path returns NEEDS_WORK with a spec-gap finding.

## Approach

1. Add a fixture under `tests/` (or `tests/fixtures/`) that encodes a status-tabs-like work-item description vs thinner acceptance/diff.
2. Drive it through the brief builder + reviewer verdict helper (or documented stub that mirrors `agents/se-reviewer.md` grading rules for this fixture) so the result is NEEDS_WORK / spec-gap.
3. Keep the test under `tests/test_phase_reviewer.py -k status_tabs` (or a dedicated file imported there). Do not edit `skills/execute-phase/SKILL.md`.

## Acceptance Criteria

### status-tabs-fixture
**criterion**: status-tabs fixture yields NEEDS_WORK with a spec-gap finding; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with pytest python -m pytest tests/test_phase_reviewer.py -q -k status_tabs; state: active

## Findings

_None._

## Constraints

_None._

## Position

### phase-reviewer
**position**: executing wave 2: status-tabs-fixture; **scope**: phase; state: active

### workflow-loop
**position**: retry-loop done; next up: phase-reviewer; **scope**: effort; state: active

## Unapplied Amendments

_None._
