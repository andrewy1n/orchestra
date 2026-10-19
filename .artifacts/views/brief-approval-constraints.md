# Brief: approval-constraints

> Derived brief — not authoritative. Composed on demand from `project:brief`; edit records, not this file.

## Work Item

### approval-constraints
**title**: Supersede dashboard-read-only constraints; **phase**: dashboard-approvals; **kind**: deliver; **effort**: workflow-loop; state: in_progress

## Description

Replace the three stale active read-only dashboard constraints with one constraint that names the allowed human-gate write set.

## Approach

1. List active constraints whose subjects are `dashboard-read-only`, `dashboard-read-only-dashboard-bugfix`, and `dashboard-read-only-dashboard-features`.
2. Create one new constraint (subject e.g. `dashboard-human-gate-writes`) stating: dashboard may write only human Needs-you clears via adaptive-artifacts CLI, using the displayed revision and a recorded decision/note as designed.
3. Supersede each of the three old constraints to the new one (or supersede each closed after the new constraint is active — follow existing constraint supersede patterns in the store).
4. Acceptance is a store check (list active constraints): none of the three old subjects remain active; the new statement is present.

## Acceptance Criteria

### approval-constraints
**criterion**: Active store has no dashboard-read-only, dashboard-read-only-dashboard-bugfix, or dashboard-read-only-dashboard-features constraint; one active constraint describes human-gate CLI writes with recorded decision/note; **method**: check; **effort**: workflow-loop; **verify_command**: adaptive-artifacts list --type project:constraint --state active | python3 -c "import sys,json; d=json.load(sys.stdin); s={r['subject'] for r in d['records']}; assert not s & {'dashboard-read-only','dashboard-read-only-dashboard-bugfix','dashboard-read-only-dashboard-features'}; assert any('human' in (r.get('payload',{}).get('statement') or r.get('body') or '').lower() or 'human' in r['subject'] for r in d['records'])"; state: active

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
