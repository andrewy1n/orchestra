---
{
  "id": "rec-3aabaa06-d6f4-4a09-8e86-4a26c2612071",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "approval-dismiss-subagent",
    "decisions": [
      "dashboard-approvals-scope",
      "approval-revision-guard"
    ],
    "depends_on": [
      "approval-contract"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 40,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "dashboard-approvals",
    "requirements": [
      "R4",
      "R5",
      "R6"
    ],
    "size": "M",
    "title": "Dismiss CLI with revision and notes"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-14T07:27:57+00:00",
  "relationships": {},
  "revision": "sha256:25ce49e1ee4feb42f3fc8c311fe51a70a1ed443cf0a98b549c7baefcafaefc9b",
  "subject": "approval-dismiss"
}
---

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
