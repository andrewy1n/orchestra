# Brief: verify-dashboard-approvals

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### verify-dashboard-approvals
**title**: Verify dashboard approvals with evidence; **phase**: dashboard-approvals; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Prove the phase exit criteria hold together: run the Textual app entry-point pilots for the approval flow, then the constraint/README/skill checks.

## Approach

1. Run the focused approval pilots through `tests/test_dashboard_app.py` (real dashboard entry) covering detail-first dismiss, confirm actions with notes, and stale-revision refusal.
2. Confirm stale read-only constraints are gone and the human-gate write constraint is active.
3. Confirm README keys and skill↔contract consistency for any field mentions.
4. Do not use an unfiltered full `tests` tree or unfiltered `test_dashboard_app.py` as a verification acceptance.

## Acceptance Criteria

### verify-dashboard-approvals
**criterion**: Through the Textual dashboard app entry point: list d opens detail with no write; confirm/cancel and Approve/Reject/Sign/Accept-risk behave as specified with notes; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k approval; state: active

### verify-dashboard-approvals-constraints
**criterion**: Stale never-writes dashboard constraints superseded; dashboard-human-gate-writes active with human-gate write policy; **method**: check; **effort**: workflow-loop; **verify_command**: /home/andrewyin/adaptive-artifacts/bin/adaptive-artifacts --store /home/andrewyin/se-workflow/.artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); stmts=[(r['subject'], (r.get('payload') or {}).get('statement') or '') for r in d['records']]; assert any(s=='dashboard-human-gate-writes' for s,_ in stmts); hg=[t for s,t in stmts if s=='dashboard-human-gate-writes']; assert hg and ('human Needs-you' in hg[0] or 'human-gate' in hg[0].lower()); old={'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert not any('never writes' in t.lower() for s,t in stmts if s in old); assert all('Retired' in t or 'dashboard-human-gate-writes' in t for s,t in stmts if s in old)"; state: active

### verify-dashboard-approvals-docs
**criterion**: README keys updated; skill↔contract consistency green when skills mention the new optional note fields; **method**: check; **effort**: workflow-loop; **verify_command**: grep -E 'Approve|Reject|Accept risk' README.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q; state: active

### verify-dashboard-approvals-revision
**criterion**: Stale displayed revision shows a visible message and skips the write; no @current retry; **method**: tdd; **effort**: workflow-loop; **verify_command**: uv run --with textual --with pytest python -m pytest tests/test_dashboard_app.py -q -k 'approval and stale'; state: active

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
