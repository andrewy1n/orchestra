---
{
  "id": "rec-a003bfbb-05e4-4554-a50a-1dd54ac40bdf",
  "lifecycle_state": "superseded",
  "payload": {
    "effort": "packaging",
    "phase": "version-compat-check",
    "source": "session",
    "status": "promoted"
  },
  "record_type": "plan:backlog-item",
  "recorded_at": "2026-10-15T07:55:00+00:00",
  "relationships": {
    "supersedes": [
      "rec-ee7c1916-1baa-47a7-b7b2-31974bf0339a"
    ]
  },
  "revision": "sha256:f0f35c2cc12f041980a62d4536e36d89ae1b386f7d471e913ad6cf558ac55ee4",
  "subject": "version-compat-check",
  "time": {
    "as_of": "2026-10-15T07:50:12+00:00"
  }
}
---

# Version flag + compatibility check

Add adaptive-artifacts --version and have se-workflow check that the two versions are compatible.
