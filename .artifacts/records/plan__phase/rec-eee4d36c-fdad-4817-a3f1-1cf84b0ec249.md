---
{
  "id": "rec-eee4d36c-fdad-4817-a3f1-1cf84b0ec249",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "monorepo",
    "ordinal": 4,
    "title": "Host cutover"
  },
  "record_type": "plan:phase",
  "recorded_at": "2026-10-27T07:46:13+00:00",
  "relationships": {},
  "revision": "sha256:ab61f5b8e4c0f555839c8c8233d8c6d91c751ee64c2093ee3db8cc8af44f3cc7",
  "subject": "monorepo-cutover"
}
---

## Problem

The adaptive-artifacts plugin is still installed, so session hooks fire twice.

## Approach

With owner approval, uninstall the plugin and its marketplace entry, then check a new session.

## Exit criteria

One handoff per session start and one hook-stop per stop.
