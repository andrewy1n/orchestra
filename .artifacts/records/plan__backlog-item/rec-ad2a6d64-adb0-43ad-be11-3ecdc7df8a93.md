---
{
  "id": "rec-ad2a6d64-adb0-43ad-be11-3ecdc7df8a93",
  "lifecycle_state": "active",
  "payload": {
    "effort": "packaging",
    "phase": "plugin-root-and-cli",
    "source": "session",
    "status": "promoted"
  },
  "record_type": "plan:backlog-item",
  "recorded_at": "2026-10-14T08:17:25+00:00",
  "relationships": {
    "supersedes": [
      "rec-27f88ac4-58dd-47b7-9c00-92acdd63716f"
    ]
  },
  "revision": "sha256:446dfebfef4b2bc887368a2348cf7fd4ec6102db4f90f8bbd733649829c6f4a3",
  "subject": "plugin-root-paths",
  "time": {
    "as_of": "2026-10-14T08:17:25+00:00"
  }
}
---

# Replace guessed paths with plugin-root vars

Replace guessed paths with `${CLAUDE_PLUGIN_ROOT}` in skills (and `${CURSOR_PLUGIN_ROOT}` for Cursor). Right now three places guess where adaptive-artifacts lives, each in a different order, and they fall back to assuming `~/adaptive-artifacts`.
