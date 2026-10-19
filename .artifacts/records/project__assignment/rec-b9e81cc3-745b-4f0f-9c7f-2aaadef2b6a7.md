---
{
  "base_kind": "instruction",
  "id": "rec-b9e81cc3-745b-4f0f-9c7f-2aaadef2b6a7",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "skills-handoff",
    "work_item": "skills-claim-handoff"
  },
  "provenance": {
    "sources": [
      "skills-claim-handoff"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-16T19:16:20+00:00",
  "relationships": {},
  "revision": "sha256:59bf90e97f23ea5b158d59442caf75582810901f0114e1220dc8291d93998b38",
  "subject": "skills-claim-handoff",
  "time": {
    "observed": "2026-10-16T19:16:20+00:00",
    "recorded": "2026-10-16T19:16:20+00:00"
  }
}
---

## Orientation

Worktree only: `/home/andrewyin/affidavit--atomic-claims` on branch `phase/atomic-claims`. Do not edit `.artifacts/` (parent owns store on `/home/andrewyin/affidavit`). Do not call `adaptive-artifacts`. After code lands, commit excluding `.artifacts`:
`git add -A -- . ':!.artifacts' && git commit -m "skills-claim-handoff"`
Return evidence with that commit SHA as `revision`.

Territory: `skills/plan-phase/SKILL.md`, `skills/discuss/SKILL.md`, `skills/execute-phase/SKILL.md`, and `skills/verify-work/SKILL.md` only if criterion-as-claim wording must change. Do not edit `contract/` or `tests/` (sibling tasks). Solo wave. Contract change for optional criterion already landed on this branch (commit f9d7371) — examples may omit criterion or use empty string.

### Requirements

R1: Every `deliver` or `repair` work-item carries one or more atomic requirement ids in `payload.requirements` (comma-separated). When no `project:specification` exists for the phase, the work-item `## Description` is the id'd list (each id names one observable behavior). `incidental` work stays exempt; `evaluate` follows campaign rules and is out of this phase's force.

R2: Each acceptance for deliver/repair names exactly one requirement id in `payload.requirement`. That id must appear on its work-item. Compound ids (commas, "and"-bundled surfaces, multiple observables under one Rn) are refused by skill lint and consistency tests.

R3: New acceptances are thin: no criterion prose. Skills write `criterion` as empty or omit it once the contract allows. Done meaning lives on the requirement text (specification `## Requirements`, or the work-item description when there is no spec), not on a re-summary field.

R5: `execute-phase` assignment briefs carry record ids and quote the original work-item Description/Approach and the requirement text for each linked id. They do not re-summarize the claim. Subagents receive that brief text verbatim.

### Design Invariants

- For deliver/repair, coverage by requirement id means one acceptance naming that single id.
- Derived acceptance lines do not depend on criterion prose to render.
- claim-witnesses store-authority for check-runs remains the close gate.

### Design Assumptions

- Existing acceptances with fat criterion remain readable; new planning follows thin rules.
- Dashboard label polish can lag (may show requirement id when criterion is empty).
- evaluate/incidental keep today's looser requirement rules unless a later phase says otherwise.

### Decisions

- atomic-claims-enforcement: skills + contract only (optional criterion, view requires_payload cleanup; no close-time lint)
- thin-acceptance-shape: no criterion prose; criterion optional_payload; brief/plan/verification drop criterion from requires_payload
- atomic-deliver-repair-ids: atomic ids required on deliver/repair; description-as-list without a spec; one acceptance per id; incidental exempt
- original-text-briefs: briefs carry record ids and quote original work-item and requirement text verbatim
