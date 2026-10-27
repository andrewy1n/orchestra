---
{
  "id": "rec-6ee0e17f-652b-4f4f-ab5a-7ef6b048b9ef",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "canon-cli-ergonomics",
    "executor": "inline",
    "work_item": "discovery-hooks"
  },
  "provenance": {
    "sources": [
      "discovery-hooks"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-14T09:31:42+00:00",
  "relationships": {},
  "revision": "sha256:ddbbe4c43ef105c982eb486691d11be4d4a313dcd626fb2f9b1b4505126969d9",
  "subject": "discovery-hooks",
  "time": {
    "observed": "2026-10-14T09:31:42+00:00",
    "recorded": "2026-10-14T09:31:42+00:00"
  }
}
---

## Orientation

Worktree: /home/andrewyin/adaptive-artifacts--aa-cli-surface. Store writes stay on primary checkout.

### Requirements
R7: Worktree store discovery + session-hooks no-clobber.

### Design invariants
- Records authoritative; views derived.
- Qualified names and explicit revisions remain valid.
