---
{
  "base_kind": "task",
  "id": "rec-2a54cba9-557d-4084-a868-1445f625ad15",
  "identity": "unknown",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "suite-engine",
    "decisions": "phase-gate-shape,suite-plugin-defaults,suite-policy-authority,red-first-scope",
    "effort": "workflow-loop",
    "estimate_minutes": 25,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "verification-policy",
    "requirements": "R3,R4,R5,R7,R8",
    "size": "L",
    "title": "Suite runner + execute-phase policy"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-15T09:00:27+00:00",
  "relationships": {
    "depends_on": [
      "rec-55371815-1590-4cf2-98ec-2ee9c9c211dc"
    ]
  },
  "revision": "sha256:7adbbbf31a6dd5a30e57bdbbd6b9eacd223b981eea7c24dc0e2f687baddd1695",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "suite-engine"
}
---

## Description

Make the phase-end suite runner and execute-phase skill honor contracted `phase_gate.suite` (mode/command/gate), with `<phase>-suite` subjects and no agent waiver.

## Approach

1. Load `phase_gate.suite` from the project design (same path resolution as other project metadata).
2. Rename or wrap `affidavit/tier2.py` as the suite runner: use contracted `command` when mode is smoke/full; subject suffix `-suite`; skip start when `mode=none`; for `deferred`/`external` do not run locally.
3. Update `skills/execute-phase/SKILL.md`: replace hardcoded tier-2 steps with policy read; `required` blocks Landing; `advisory` records check-run + finding on fail and does not block; `deferred` is a Landing human stop; never allow agent skip.
4. On advisory fail: create finding (needs none or human per skill norms); do not create required-gate fix-task storms unless gate is required (keep fix-task path for required fails).
5. Leave close-batch red-first for `tdd` unchanged.
6. Extend `tests/test_tiered_verification.py` (or successor) for mode/gate matrix: none skips, required blocks, advisory allows Landing after fail record.
