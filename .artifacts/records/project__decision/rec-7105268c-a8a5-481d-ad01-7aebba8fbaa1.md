---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-7105268c-a8a5-481d-ad01-7aebba8fbaa1",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "any pytest fail at base counts",
    "choice": "red must be fail with assertion-level failing node; import/collection-only insufficient",
    "effort": "workflow-loop",
    "phase": "oracle-witnesses"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-16T19:47:00+00:00",
  "relationships": {},
  "revision": "sha256:c25e0188b478683817c463d053f271addb6ad4e763eacea2537a16130814932f",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "assertion-level-red",
  "time": {
    "as_of": "2026-10-16T19:47:00+00:00"
  }
}
---

## Rationale

Test-first only helps if the red shows the oracle can discriminate wrong behavior. Requiring `result: fail` plus a failing node whose output is assertion-level rejects import/collection reds that any missing symbol produces — those do not prove the test would catch a wrong implementation.

## Counter-argument

Accepting any pytest fail at base is simpler and needs no output classification. The cost is closing the discrimination hole: an oracle that only fails to import still "goes red," then goes green when the executor adds a stub, without ever asserting the requirement.
