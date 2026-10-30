---
{
  "id": "rec-10a91d58-391b-4ac4-baf4-cfce4f8b858f",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "area-state",
    "result": "pass",
    "revision": "8462fda2c212675d225e18eacb47a2322ecdefa1",
    "verdict": "pass",
    "work_item": "area-state"
  },
  "record_type": "conductor:execution-report",
  "recorded_at": "2026-10-30T08:05:42+00:00",
  "relationships": {},
  "revision": "sha256:a33574014958f53a1526c0e74504219c9001b1814cb7d66e7a32b38e0ca441e8",
  "subject": "area-state"
}
---

subject: area-state
kind: deliver
result: pass
revision: 8462fda2c212675d225e18eacb47a2322ecdefa1
evidence:
- npm run lint: pass (70 files)
- npm run check: pass (0 errors, 0 warnings, api-types:check ok)
- npm test: pass (19 files, 121 tests)
- vitest src/effortRoute.test.ts -t "R18 " and src/lib/state/areas.test.ts: both verify_commands print true
observations: Tests were written first and failed on the missing effortHref function, not on an assertion. railItems and breadcrumbParts take an optional fourth argument "selected" for routes without an effort in the path (journal, record). EffortRail still calls polling.selectEffort on click; the rail task rewires it.
verdict: pass
needs_human: false
