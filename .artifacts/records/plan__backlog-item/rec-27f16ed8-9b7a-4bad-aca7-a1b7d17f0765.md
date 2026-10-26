---
{
  "id": "rec-27f16ed8-9b7a-4bad-aca7-a1b7d17f0765",
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
      "rec-7fd510b5-a37a-419f-b45f-453807923fcc"
    ]
  },
  "revision": "sha256:43f5bfd18317b242ab5efa0501bfb4b918092d025d18f802c6fc2338348592e2",
  "subject": "close-batch-subcommand",
  "time": {
    "as_of": "2026-10-14T08:17:25+00:00"
  }
}
---

# close_batch as se-workflow subcommand

Turn close_batch.py into a se-workflow close-batch subcommand, so skills only ever call se-workflow or adaptive-artifacts.
