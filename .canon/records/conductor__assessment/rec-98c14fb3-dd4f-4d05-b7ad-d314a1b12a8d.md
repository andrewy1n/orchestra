---
{
  "id": "rec-98c14fb3-dd4f-4d05-b7ad-d314a1b12a8d",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "session-handoff",
    "missing": "",
    "next": "release",
    "phase": "hook-context-budget",
    "requirement": "R7",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-29T08:34:53+00:00",
  "relationships": {},
  "revision": "sha256:91b45e853909018496147f7f60d3a20be2252b892aa6d55f08e81951e7ad5973",
  "subject": "hook-context-budget-R7"
}
---

## Evidence

Green check-run rec-806c0bc1-1bdb-428d-90ac-5bdc82075928 at 09561d29d. Assertion-level red check-run rec-6373cfc6-2a75-4cf3-a121-5502252b1e06 at e6b7d1957, an ancestor of 09561d29d. tests/test_hooks.py matches its frozen oracle hash 656488cb.

## Missing

none

## Reason

The frozen oracle went from assertion-level red to green on a descendant revision with the oracle file unchanged.
