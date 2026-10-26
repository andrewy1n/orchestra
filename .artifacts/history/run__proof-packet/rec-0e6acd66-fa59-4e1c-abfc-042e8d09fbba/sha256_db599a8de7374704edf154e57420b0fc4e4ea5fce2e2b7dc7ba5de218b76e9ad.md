---
{
  "id": "rec-0e6acd66-fa59-4e1c-abfc-042e8d09fbba",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "8056506dde91a10d10e8e7bcda33d2ff0a0324f0",
    "effort": "dashboard",
    "kind": "demo",
    "phase": "deep-links",
    "revision": "506b97b205c65e9f929379c3a3f656a09e7376f1"
  },
  "provenance": {
    "sources": [
      "deep-links"
    ]
  },
  "record_type": "run:proof-packet",
  "recorded_at": "2026-10-20T04:43:56+00:00",
  "relationships": {},
  "revision": "sha256:db599a8de7374704edf154e57420b0fc4e4ea5fce2e2b7dc7ba5de218b76e9ad",
  "subject": "deep-links",
  "time": {
    "observed": "2026-10-20T04:43:56+00:00",
    "recorded": "2026-10-20T04:43:56+00:00"
  }
}
---

## Look

Open a task overlay whose description cites a `rec-…` id or another task; the token is a link and opens the matching overlay. Milestone subjects expand the named group.

## Machine

- phase head: 506b97b205c65e9f929379c3a3f656a09e7376f1
- base: 8056506dde91a10d10e8e7bcda33d2ff0a0324f0
- vitest: links.test.ts + deepLinks.test.ts pass
- review check-run: rec-b2518fc1-75e3-4270-a9b9-a0f4dbef72b6
- integration-report: deep-links pass

## Attention

Hard-refresh the dashboard so `index-BmId3bit.js` loads. Follow one linkified reference in a live detail view.

## Diff

```
 dashboard/web/ui/src/App.svelte        |  83 +++++++++-
 dashboard/web/ui/src/deepLinks.test.ts | 293 +++++++++++++++++++++++++++++++++
 dashboard/web/ui/src/links.test.ts     | 156 ++++++++++++++++++
 dashboard/web/ui/src/links.ts          | 199 ++++++++++++++++++++++
 dashboard/web/ui/src/markdown.ts       |  23 ++-
 dashboard/web/ui/src/router.ts         |   4 +-
 6 files changed, 747 insertions(+), 11 deletions(-)
```
