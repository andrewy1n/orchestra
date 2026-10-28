---
{
  "id": "rec-eb7b1b4e-a39e-4a38-a5cc-6db68976ac1c",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "backlog-to-idea-review",
    "effort": "composer",
    "evidence_kind": "review",
    "method": "review",
    "result": "fail",
    "revision": "477f2ad42e859e901710fd6f8554ecf74c0480df",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T06:30:03+00:00",
  "relationships": {},
  "revision": "sha256:a589e8ff5a8c5f2b5f944122802d1b91bdf2040701dea02126e44a1030c081ed",
  "subject": "backlog-to-idea-review"
}
---

verdict: NEEDS_WORK
findings:
  - task: idea-views-engage
    kind: missing-test
    expected: tests/test_views.py covers an open idea, a dismissed idea and an idea without effort (R8 effort filter).
    observed: tests/test_views.py keeps only the open and dismissed cases. The effort filter is covered only by the frozen oracle tests/test_idea_view.py.
    severity: minor
integration:
  interfaces: Consumers read composer:idea; score drops backlog-item and feedback; live store converted.
  assumptions: R3, R4 and R7 judged from the primary store read-only.
  invariants: R1 to R16 hold; 21 active ideas; live validate valid; scan clean.
  conflicts: none
