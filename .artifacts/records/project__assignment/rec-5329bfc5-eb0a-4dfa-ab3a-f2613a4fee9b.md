---
{
  "base_kind": "instruction",
  "id": "rec-5329bfc5-eb0a-4dfa-ab3a-f2613a4fee9b",
  "identity": "unknown",
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
  "record_type": "project:assignment",
  "recorded_at": "2026-10-16T19:13:42+00:00",
  "relationships": {},
  "revision": "sha256:fbac3c6b6d538ca510d5a006d3307c2bb839487f31b48804ae0f1d8a28525ba2",
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
