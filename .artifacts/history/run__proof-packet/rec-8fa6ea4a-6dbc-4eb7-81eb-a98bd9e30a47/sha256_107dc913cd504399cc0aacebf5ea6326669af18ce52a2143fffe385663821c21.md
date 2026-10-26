---
{
  "id": "rec-8fa6ea4a-6dbc-4eb7-81eb-a98bd9e30a47",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "259e38ae979beedc83898c481e9948689932c732",
    "effort": "dashboard",
    "kind": "demo",
    "phase": "phase-overview",
    "revision": "42d8187d49206aeb1ee9de8cae589935123d6e0b"
  },
  "provenance": {
    "sources": [
      "phase-overview"
    ]
  },
  "record_type": "run:proof-packet",
  "recorded_at": "2026-10-20T04:51:27+00:00",
  "relationships": {},
  "revision": "sha256:107dc913cd504399cc0aacebf5ea6326669af18ce52a2143fffe385663821c21",
  "subject": "phase-overview",
  "time": {
    "observed": "2026-10-20T04:51:27+00:00",
    "recorded": "2026-10-20T04:51:27+00:00"
  }
}
---

## Look

Open a phase overlay and switch Overview → Spec → Tasks. Shared chrome (chips, progress, next, requirements, waves) stays; tab bodies are section cards. Home layout unchanged.

## Machine

- revision: 42d8187d49206aeb1ee9de8cae589935123d6e0b
- base: 259e38ae979beedc83898c481e9948689932c732
- vitest phaseOverview.test.ts pass
- review + integration pass

## Attention

Hard-refresh the dashboard. Discuss home/main left-heavy layout next (deferred).

## Diff

```
 dashboard/web/ui/src/App.svelte            |  66 +++++-
 dashboard/web/ui/src/app.css               | 113 +++++++++++
 dashboard/web/ui/src/detailView.ts         |  14 +-
 dashboard/web/ui/src/phaseChrome.ts        | 137 +++++++++++++
 dashboard/web/ui/src/phaseOverview.test.ts | 314 +++++++++++++++++++++++++++++
 5 files changed, 636 insertions(+), 8 deletions(-)
```
