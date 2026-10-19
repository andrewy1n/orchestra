# Brief: approval-confirm-ux

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### approval-confirm-ux
**title**: Detail-first confirm UX and README keys; **phase**: dashboard-approvals; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Turn Needs-you dismiss into a detail-first confirm flow with kind-specific evidence, approve/reject (or sign / accept-risk) actions, and README key updates.

## Approach

1. List `d` on a human-dismissible item opens Needs-you detail and does not call dismiss CLI; non-human kinds keep refuse behavior.
2. Enrich detail evidence: unsigned-check (check-run body, acceptance, revision vs HEAD); plan-review / questions (phase body with approach, tasks, Landing, run facts when scope is plan-review); finding (claim, basis, Evidence/Consequence).
3. From detail, open a confirm modal: Approve/Reject/Cancel for questions (distinct keys for Approve vs Reject); Sign/Cancel for manual checks; Accept risk/Cancel for findings. Require a one-line note for Reject and Accept risk; optional otherwise.
4. On confirm, call the dismiss layer with the displayed item revision and note; on cancel, make no CLI call; on stale revision, show that the item changed since opened and refresh.
5. Update README key table for the new bindings and flow.
6. Pilot tests in `tests/test_dashboard_app.py` with `-k approval` for detail-first, confirm/cancel, reject+note, stale message, and action outcomes through the Textual app.

## Acceptance Criteria

### approval-confirm-ux
**criterion**: From the Needs-you list, d opens detail and does not write; a write requires detail plus confirm; cancel makes no CLI call; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (detail or confirm or cancel)'; state: active

### approval-confirm-ux-actions
**criterion**: Plan-review Approve/Reject, manual Sign, and finding Accept risk behave as specified with note rules; Reject keeps the question open; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and (approve or reject or sign or accept)'; state: active

### approval-confirm-ux-readme
**criterion**: README key table documents detail-first d, confirm actions (Approve/Reject/Sign/Accept risk), and note rules; **method**: check; **effort**: workflow-loop; **verify_command**: grep -E 'Approve|Reject|Accept risk|Sign' README.md && grep -E 'Needs you|dismiss|confirm' README.md; state: active

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
