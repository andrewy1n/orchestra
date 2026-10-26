---
{
  "id": "rec-b84d2ec4-e9a3-42b4-adcf-334bf3a0e572",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "inline",
    "decisions": [
      "oracle-red-surface"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 10,
    "executor": "inline",
    "kind": "deliver",
    "phase": "evidence-authority",
    "requirements": [
      "R9"
    ],
    "size": "S",
    "title": "Refuse clearly when aff missing for assertion-red"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-21T07:07:26+00:00",
  "relationships": {},
  "revision": "sha256:3cca0aa3267886d51129b26e5cee9ff0fa1257f6431e826aa80a7b03188f11a9",
  "subject": "fix-oracle-red-missing-aff"
}
---

## Description

R9: When aff assertion-red CLI is missing, oracle-backed close refuses with a clear CloseRefused/OracleAdapterUnavailable message (already partly true); ensure FileNotFoundError path is covered and pre-existing oracle CLI tests fail clearly without PATH aff rather than confusing runner errors.

## Approach

Harden _assertion_level_red FileNotFoundError handling if needed; add/adjust a unit test that missing aff is refused with assertion/oracle messaging.
