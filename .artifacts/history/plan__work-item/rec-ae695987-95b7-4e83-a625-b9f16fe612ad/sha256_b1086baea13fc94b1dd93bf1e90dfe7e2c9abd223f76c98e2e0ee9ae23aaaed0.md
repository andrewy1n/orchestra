---
{
  "id": "rec-ae695987-95b7-4e83-a625-b9f16fe612ad",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "depends_on": [
      "tm-parse-events"
    ],
    "effort": "session-analysis",
    "kind": "deliver",
    "phase": "transcript-metrics",
    "title": "Tool call, error and retry counts"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-02T01:32:27+00:00",
  "relationships": {},
  "revision": "sha256:b1086baea13fc94b1dd93bf1e90dfe7e2c9abd223f76c98e2e0ee9ae23aaaed0",
  "subject": "tm-tool-metrics"
}
---

## Description

Count tool_use by name, tool_result errors by is_error, and retries (same tool and input repeated after an error). Waits on the reader.
