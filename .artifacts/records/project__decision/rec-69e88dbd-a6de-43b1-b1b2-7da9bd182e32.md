---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-69e88dbd-a6de-43b1-b1b2-7da9bd182e32",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Keep --expected-revision @current",
    "choice": "Writes use the displayed record revision; never @current for these dismissals",
    "effort": "workflow-loop",
    "phase": "dashboard-approvals"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-11T06:26:07+00:00",
  "relationships": {},
  "revision": "sha256:ad2f8b563710b1287ad1cbce242fd4f79faa38b4742fe5404f205ddf97698b1a",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "approval-revision-guard",
  "time": {
    "as_of": "2026-10-11T06:26:07+00:00"
  }
}
---

## Rationale

`--expected-revision @current` skips conflict detection: the dashboard can clear a gate the agent changed after render. Passing the displayed revision makes concurrent updates visible and forces a refresh, which is the correct human-in-the-loop behavior.

## Counter-argument

`@current` always succeeds and matches a prior request wording in the issue thread. The cost is approving invisible changes — the bug this phase exists to fix.
