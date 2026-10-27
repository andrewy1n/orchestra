---
{
  "id": "rec-a0c9fa27-5d8a-4f8d-9de6-175ffed667a8",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "deep-links-wire-agent",
    "decisions": [
      "deep-links-surfaces",
      "deep-links-labels"
    ],
    "depends_on": [
      "deep-links-resolve"
    ],
    "effort": "dashboard",
    "estimate_minutes": 15,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "deep-links",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R5",
      "R6"
    ],
    "size": "M",
    "title": "Wire linkify into meta and markdown"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-20T04:42:18+00:00",
  "relationships": {},
  "revision": "sha256:3b27b305a18dc48849dbf83c7a389a113e0f4e4a738825fb3f7e78c9f1e0e1d8",
  "subject": "deep-links-wire"
}
---

## Description

R1: In detail and list surfaces that show a task id, activating the control opens the task overlay for that id when the task exists in the current snapshot.
R2: A phase subject reference navigates to the phase overlay for the selected effort (or the effort named beside the reference when present).
R3: A requirement id reference opens the requirement overlay when effort and phase context are known.
R5: A milestone subject reference selects or expands that milestone in the Phases block when milestone-nav is present, or navigates to a phase in that milestone when only one context applies.
R6: Rendered markdown bodies linkify the same reference shapes when they appear as standalone tokens.

## Approach

Integrate `resolveRef` into list/detail meta that currently prints raw ids, and into the markdown render path (`renderMarkdown` post-process or marked walk) so standalone tokens become `<a href="#/...">` links. Milestone refs expand/select via existing milestone-nav helpers on home. UI-test clicks in `deepLinks.test.ts` (or extend an existing UI test module).
