---
{
  "id": "rec-3a4f83f2-a0dd-43f7-8cb4-b3aef3440d1b",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "inline",
    "decisions": [
      "one-ship-scope",
      "expected-revision-default",
      "views-immutability-exempt"
    ],
    "effort": "canon-cli-ergonomics",
    "estimate_minutes": 15,
    "executor": "inline",
    "kind": "deliver",
    "phase": "aa-cli-surface",
    "requirements": [
      "R6"
    ],
    "size": "M",
    "title": "get output shaping and payload/apply ergonomics"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-14T09:31:42+00:00",
  "relationships": {},
  "revision": "sha256:6de471adcd17c6d38e9d373c9ee3fe37dc8a6b99899ccae352ea41ca8fe24f4e",
  "subject": "get-payload-apply"
}
---

## Description

get --full/--field/--body-only; repeatable -p/--set and --payload-file on mutators; apply --file for NDJSON.

## Approach

Extend cmd_get and mutator payload loading; accept apply --file PATH as alias for positional input. Tests for get field projection, --set merge, and apply --file.
