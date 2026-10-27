---
{
  "id": "rec-eee4d36c-fdad-4817-a3f1-1cf84b0ec249",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "monorepo",
    "ordinal": 4,
    "title": "Host cutover"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-27T07:46:13+00:00",
  "relationships": {},
  "revision": "sha256:88357fbf657ddd2ecdda4ad80c7cc10cb7fa32d42c32a8706ef57b0b14abc1b8",
  "subject": "monorepo-cutover"
}
---

## Problem

The adaptive-artifacts plugin is still installed, so session hooks fire twice.

## Approach

With owner approval, uninstall the plugin and its marketplace entry, then check a new session.

## Exit criteria

One handoff per session start and one hook-stop per stop.
