---
{
  "base_kind": "phase",
  "id": "rec-b78c4e43-e7d4-4de7-a6f4-f06bd88ffb15",
  "identity": "unknown",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "workflow-loop",
    "ordinal": 22,
    "title": "Oracle author, freeze, and amendments"
  },
  "record_type": "project:phase",
  "recorded_at": "2026-10-16T09:24:22+00:00",
  "relationships": {},
  "revision": "sha256:d5732e2c260dbb8bf3a60dd188ea36bae8bb74cf3c814ac3e976fe632af5a2aa",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "oracle-witnesses"
}
---

## Problem

The same agent writes the code, the tests, and chooses verify_command. Nothing checks that the oracle can tell a wrong implementation from a right one. Frozen hashes and a separate oracle author are the intended fix.

## Approach

not yet scoped — discuss when this phase is current. Direction: oracle-author subagent from spec text, assertion-level red via aff check, freeze test ids/hashes on acceptances, amendments approved by the parent session (decision amendment-approver).

## Exit criteria

Decide at plan-phase. At minimum: a requirement can only close when its frozen oracle tests failed at base on an assertion and pass at head unchanged or with an approved amendment.
