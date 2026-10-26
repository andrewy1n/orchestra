---
{
  "id": "rec-7105268c-a8a5-481d-ad01-7aebba8fbaa1",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "any pytest fail at base counts",
    "choice": "red must be fail with assertion-level failing node; import/collection-only insufficient",
    "effort": "workflow-loop",
    "phase": "oracle-witnesses"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-16T19:47:00+00:00",
  "relationships": {},
  "revision": "sha256:67aab0d2b33a1df8ea3a1b1ca4f7a152b95db830fb39e793fb7e3790824aec92",
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
