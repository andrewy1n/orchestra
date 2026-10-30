---
{
  "id": "rec-6a6c09fb-c0ff-4c50-b2ac-5b46dee0e474",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sonnet-fix-hook-dropped-groups",
    "decisions": [
      "hook-context-shape",
      "hook-constraints-scope"
    ],
    "effort": "session-handoff",
    "estimate_minutes": 10,
    "executor": "subagent",
    "kind": "repair",
    "phase": "hook-context-budget",
    "requirements": [
      "R5",
      "R14"
    ],
    "size": "S",
    "title": "Keep effortless and off-slug items in the start hook"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T09:17:10+00:00",
  "relationships": {},
  "revision": "sha256:2825af72e26de94962ecc07e04cd85706c1702a8bc44b1d43ed8a4c7cb695e9a",
  "subject": "fix-hook-dropped-groups"
}
---

## Description

Fix review findings review-compact-hook-view-behavior-bug, review-compact-hook-view-missing-test and review-compact-hook-view-spec-gap.

R5: The constraints block omits constraints whose effort is closed.
R14: Every Needs Human and Blocking Question item that `orchestra handoff` shows appears in the start hook context or is named on its omitted line, even when the item belongs to no live effort.

## Approach

In orchestra/views.py, `hook_handoff_sections` keeps every HOOK_VIEW group, not only live-effort groups: live efforts first in position order (newest first), then the remaining groups alphabetically. The hook budget and omitted line treat them like any section. `live_efforts` counts only active score:effort records whose status is not closed; positions no longer make an effort live.
