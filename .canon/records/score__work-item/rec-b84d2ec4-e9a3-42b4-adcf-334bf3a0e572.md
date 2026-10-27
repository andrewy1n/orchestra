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
  "record_type": "score:work-item",
  "recorded_at": "2026-10-21T07:07:26+00:00",
  "relationships": {},
  "revision": "sha256:3d93a1f3868b6eb20e8bd4c40e14a082419736300707e3c134c3e5911aa5c6d7",
  "subject": "fix-oracle-red-missing-aff"
}
---

## Description

R9: When aff assertion-red CLI is missing, oracle-backed close refuses with a clear CloseRefused/OracleAdapterUnavailable message (already partly true); ensure FileNotFoundError path is covered and pre-existing oracle CLI tests fail clearly without PATH aff rather than confusing runner errors.

## Approach

Harden _assertion_level_red FileNotFoundError handling if needed; add/adjust a unit test that missing aff is refused with assertion/oracle messaging.
