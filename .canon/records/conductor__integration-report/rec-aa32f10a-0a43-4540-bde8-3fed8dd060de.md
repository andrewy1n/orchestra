---
{
  "id": "rec-aa32f10a-0a43-4540-bde8-3fed8dd060de",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "phase": "phase-reviewer",
    "result": "pass",
    "revision": "11a147e75daa100a2fbca2202399205b480b42e9"
  },
  "provenance": {
    "sources": [
      "phase-reviewer"
    ]
  },
  "record_type": "conductor:integration-report",
  "recorded_at": "2026-10-11T06:57:27+00:00",
  "relationships": {},
  "revision": "sha256:27a53dd273fb51918dd0d002694d965e290c50793ac0f86c176e2fbb53cd4858",
  "subject": "phase-reviewer",
  "time": {
    "observed": "2026-10-11T06:57:27+00:00",
    "recorded": "2026-10-11T06:57:27+00:00"
  }
}
---

## Interfaces

agents/se-reviewer.md + se_workflow/reviewer.py + execute-phase order + tests

## Assumptions

Graded from brief and tree at 11a147e; ignored builder self-grades

## Invariants

Reviewer writes no store; brief excludes builder grades; fix routing does not reopen done; gate requires method:review at head

## Conflicts

none
