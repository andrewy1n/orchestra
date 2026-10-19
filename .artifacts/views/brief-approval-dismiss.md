# Brief: approval-dismiss

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### approval-dismiss
**title**: Dismiss CLI with revision and notes; **phase**: dashboard-approvals; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Rewrite the dismiss CLI layer so human-gate clears use the displayed revision and can carry note fields, including a Reject path that does not answer the plan-review question.

## Approach

1. Add `revision` (record revision as displayed) to `NeedsYouItem` and populate it in `dashboard/model.py` when building Needs-you items.
2. Change `dashboard/dismiss.py`: never pass `--expected-revision @current` for these clears; require the item revision; add note/action parameters.
3. Approve question → `update --transition answered` with optional `answer` note. Reject question → leave open; `create` a finding (`needs: human`) claiming plan rejected / route to discuss or plan-phase, with `resolution_note` or body rationale as designed.
4. Sign check → `correct` with `signed_by` and optional `signed_note`, plus expected revision if the CLI supports it on correct (else document and guard at the app layer).
5. Accept risk → `update` finding `needs: none` with `resolution_note`.
6. Surface stale-revision CLI errors as `DismissError` with a clear message for the UI.
7. Tests under `-k approval` covering argv shapes, reject-does-not-answer, and stale refusal (unit or seeded CLI).

## Acceptance Criteria

### approval-dismiss
**criterion**: dismiss_command uses displayed revision (never @current); Approve/Sign/Accept-risk payloads include note fields when provided; Reject creates a needs:human finding and does not answer the continuity-question; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py tests/test_dashboard_model.py -q -k 'approval and (dismiss or revision or reject)'; state: active

### approval-dismiss-stale
**criterion**: When the CLI rejects a stale expected-revision, dismiss raises a clear error and does not retry with @current; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale'; state: active

## Findings

_None._

## Constraints

### dashboard-human-gate-writes
**statement**: The dashboard may write to the artifact store only for human Needs-you gates (continuity-question answer/reject-routing, unsigned manual check sign, finding accept-risk) via the adaptive-artifacts CLI, using the displayed record revision and a recorded decision or note as designed.; **applies_to**: dashboard/dismiss.py and dashboard Needs-you confirm UX; **effort**: workflow-loop; state: active

## Basis

needs-you-close established that human gates clear through the CLI. dashboard-approvals requires detail + confirm, displayed-revision guards, and recorded notes. A blanket read-only constraint is stale; this constraint names the allowed write set.

### dashboard-read-only
**statement**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; **applies_to**: superseded — do not enforce; **effort**: workflow-loop; state: active

## Basis

Superseded for dashboard-approvals: blanket read-only is replaced by active constraint `dashboard-human-gate-writes` (human Needs-you clears via CLI with displayed revision and recorded note).

### dashboard-read-only-dashboard-bugfix
**statement**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; **applies_to**: superseded — do not enforce; **effort**: workflow-loop; state: active

## Basis

Superseded for dashboard-approvals: blanket read-only is replaced by active constraint `dashboard-human-gate-writes` (human Needs-you clears via CLI with displayed revision and recorded note).

### dashboard-read-only-dashboard-features
**statement**: Retired: see active constraint dashboard-human-gate-writes for the allowed dashboard human-gate write set.; **applies_to**: superseded — do not enforce; **effort**: workflow-loop; state: active

## Basis

Superseded for dashboard-approvals: blanket read-only is replaced by active constraint `dashboard-human-gate-writes` (human Needs-you clears via CLI with displayed revision and recorded note).

## Position

### dashboard-approvals
**position**: dashboard-approvals planned; waiting on plan review; **scope**: phase; state: active

### phase-reviewer
**position**: phase-reviewer done; next up: tiered-verification; **scope**: phase; state: active

### workflow-loop
**position**: tiered-verification done; next up: dashboard-approvals; **scope**: effort; state: active

## Unapplied Amendments

_None._
