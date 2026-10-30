---
{
  "id": "rec-9b7eba72-490c-427b-bf0b-1fca7c9f4bbe",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "App.svelte always renders SideRail. On # and #/area/<s> polling.effort is the first visible effort. The R17 test scans only main.",
    "claim": "spec-gap on phase: the side rail shows another effort's Backlog, Needs-you and journal panels beside the product index and the area page",
    "effort": "dashboard",
    "invalidated_when": "fix lands and reviewer re-run passes, or human clears",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-30T08:56:13+00:00",
  "relationships": {},
  "revision": "sha256:8e1fb4fdb7da2871a589d78f61d20bfa317e4061894d4c87bb5dda9e14672aee",
  "subject": "review-area-levels-sidebar-levels"
}
---

## Evidence

App.svelte always renders SideRail. On # and #/area/<s> polling.effort is the first visible effort. The R17 test scans only main.

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Human: hide the side rail above the effort level (recommended), or accept it.
