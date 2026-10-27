---
{
  "id": "rec-eee4d36c-fdad-4817-a3f1-1cf84b0ec249",
  "lifecycle_state": "done",
  "payload": {
    "effort": "monorepo",
    "ordinal": 4,
    "title": "Host cutover"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-27T21:08:45+00:00",
  "relationships": {},
  "revision": "sha256:6dd0f9af80de8476190980db3947d8d6b4a214a000a6f01cfe9920f5b048b632",
  "subject": "monorepo-cutover"
}
---

## Problem

The adaptive-artifacts plugin is still installed, so session hooks fire twice.

## Approach

With owner approval, uninstall the plugin and its marketplace entry, then check a new session.

## Exit criteria

One handoff per session start and one hook-stop per stop.
