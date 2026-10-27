---
{
  "id": "rec-5329bfc5-eb0a-4dfa-ab3a-f2613a4fee9b",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "contract-thin",
    "work_item": "contract-thin-criterion"
  },
  "provenance": {
    "sources": [
      "contract-thin-criterion"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-16T19:13:42+00:00",
  "relationships": {},
  "revision": "sha256:7d29b3a74a68e3c7d6b1153c2f21c8fcf132f5a1b18d40ea4b831de0bce4b997",
  "subject": "contract-thin-criterion",
  "time": {
    "observed": "2026-10-16T19:13:42+00:00",
    "recorded": "2026-10-16T19:13:42+00:00"
  }
}
---

## Orientation

Worktree only: `/home/andrewyin/affidavit--atomic-claims` on branch `phase/atomic-claims`. Do not edit `.artifacts/` (parent owns store on `/home/andrewyin/affidavit`). Do not call `adaptive-artifacts`. After code lands, commit excluding `.artifacts`:
`git add -A -- . ':!.artifacts' && git commit -m "contract-thin-criterion"`
Return evidence with that commit SHA as `revision`.

Territory: `contract/project-design.json` only (and sync `.artifacts/project-design.json` only if that is this repo's usual post-edit step). Solo wave — no concurrent executors. Do not edit skills or tests.

### Requirements

R4: The contract makes `criterion` optional on `project:acceptance` and drops `criterion` from the acceptance `requires_payload` of the `brief`, `plan`, and `verification` views, favoring `requirement`, `method`, and `verify_command` so derived views do not lead with empty or fat prose.

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
