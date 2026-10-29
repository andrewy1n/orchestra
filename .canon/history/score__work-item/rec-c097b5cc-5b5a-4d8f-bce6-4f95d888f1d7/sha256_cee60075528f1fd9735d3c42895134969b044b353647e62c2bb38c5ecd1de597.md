---
{
  "id": "rec-c097b5cc-5b5a-4d8f-bce6-4f95d888f1d7",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "decisions": [
      "hook-context-shape",
      "hook-constraints-scope"
    ],
    "depends_on": [
      "compact-hook-view",
      "hook-budget"
    ],
    "effort": "session-handoff",
    "estimate_minutes": 5,
    "executor": "inline",
    "kind": "repair",
    "phase": "hook-context-budget",
    "requirements": [
      "R13"
    ],
    "size": "XS",
    "title": "Verify Fit session-start context under the hook cap"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T08:14:49+00:00",
  "relationships": {},
  "revision": "sha256:cee60075528f1fd9735d3c42895134969b044b353647e62c2bb38c5ecd1de597",
  "subject": "verify-hook-context-budget"
}
---

## Description

Prove the exit criteria hold together. R13: run against this repo store, the start hook returns additionalContext of at most 10,000 characters.

## Approach

Pipe `{"cwd": "<primary checkout>", "session_id": "verify"}` to `orchestra hook-start --claude` from the phase worktree and assert the additionalContext length. Then run the phase test files and the four README pytest commands.
