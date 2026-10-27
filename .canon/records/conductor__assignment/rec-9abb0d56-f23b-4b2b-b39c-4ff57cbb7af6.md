---
{
  "id": "rec-9abb0d56-f23b-4b2b-b39c-4ff57cbb7af6",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "session-analysis",
    "executor": "ag-outliers-exec",
    "work_item": "ag-outliers"
  },
  "provenance": {
    "sources": [
      "ag-outliers"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-02T01:59:09+00:00",
  "relationships": {},
  "revision": "sha256:f7952e2423a48febcc7c1202e32adeb465b5f40050a369f9774eb9babb11cc87",
  "subject": "ag-outliers",
  "time": {
    "observed": "2026-10-02T01:59:09+00:00",
    "recorded": "2026-10-02T01:59:09+00:00"
  }
}
---

## Orientation

Work in /home/ayin/se-workflow. Two parallel executors build the other two rollups. Own only scripts/session_outliers.py and tests/test_session_outliers.py. Input rows are JSON dicts shaped like the output of scripts/session_report.py --records. Scripts import each other as top-level modules, but this module needs no other script. Do not edit .artifacts/, other scripts or other tests.
