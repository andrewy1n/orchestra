---
{
  "id": "rec-7adfcdda-3afe-45c1-95cd-0214d380f5c3",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "5599749d402e1a8badbc3350d828fbc1407c9fd1",
    "effort": "dashboard",
    "kind": "demo",
    "phase": "area-levels",
    "revision": "775ca3e848e01b86c8f06d9de92d659c15c82167"
  },
  "record_type": "conductor:proof-packet",
  "recorded_at": "2026-10-30T09:27:56+00:00",
  "relationships": {},
  "revision": "sha256:314500b6cc05c5c44c11934ecef5cf8c95bb93c1f09e8f30d79045b430c897c0",
  "subject": "area-levels"
}
---

## Look

Run the dashboard on this store and open it in a browser: `uv run python -m dashboard.backend.server` from `.worktrees/area-levels` (build the UI first with `npm run build` in `dashboard/frontend`).

1. Open `#/`. You see the product index: one card for each area (Dashboard, Workflow, Evidence, and the others), each with its title, first scope sentence, effort count, open idea count and effort names. The whole card is a link. There is no left rail.
2. Click the Dashboard card. You land on `#/area/dashboard`. The breadcrumb reads `Product › Dashboard`. The left rail lists the areas. The page shows scope, stats, one Needs-you list, the effort rows, the open ideas, and any "Started as efforts" lines.
3. Click an effort row. You land on `#/effort/<name>`. The breadcrumb reads `Product › Dashboard › <effort>`, an area chip links back up, and the left rail lists the efforts of the same area.
4. Open a task, then close it. You return to the effort page.

## Machine

- Specification R1 to R31: every requirement has a verified assessment; acceptance check-runs pass at the task commits.
- Verification task verify-area-levels: e2e (3 passed), frontend lint, svelte-check, vitest (155), build, ruff, basedpyright, area Python tests, deep-link test files unchanged. All pass at head `775ca3e84`.
- Suite check-run area-levels-suite at `775ca3e84`: 1331 passed. An earlier run at 7e0a1192c failed one test (App.svelte over 150 lines); the task fix-area-levels-app-size fixed it.
- Review check-runs: first review NEEDS_WORK at 7aa726868; second review NEEDS_WORK at f4ce9b809; the check-run at head is a signed human waiver, not a reviewer verdict.
- Findings: all nine review-area-levels findings have needs none. Two judgment findings were cleared by the user's answer, three by the user's choice to fix them.

## Attention

- No reviewer has read the final delta (the second fix task, the key-handler move and the merge of main). The user waived a third review.
- dialogs.test.ts changed one line (mount route); see decision dialogs-test-mount-route.
- The old phase link on moved ideas is gone on purpose.
- `AreaIdea.area` in `GET /api/areas` now carries the idea's own area, not the listing area's subject; the response shape is the same.
- Playwright e2e ran locally only against the seeded temporary store, not against the real store.

## Diff

```
 dashboard/backend/areas.py                         |  19 +-
 dashboard/frontend/e2e/app.spec.ts                 |  13 +-
 dashboard/frontend/e2e/serve.py                    |   6 +-
 dashboard/frontend/src/App.svelte                  |  72 ++++---
 dashboard/frontend/src/app.css                     | 148 ++++++++++++--
 dashboard/frontend/src/appSource.ts                |   3 +-
 dashboard/frontend/src/detail.ts                   |  11 +-
 dashboard/frontend/src/effortRoute.test.ts         | 105 ++++++++++
 dashboard/frontend/src/lib/screens/Area.svelte     | 119 +++++++-----
 dashboard/frontend/src/lib/screens/AreaCard.svelte |  29 +++
 .../frontend/src/lib/screens/Breadcrumb.svelte     |  26 +++
 .../frontend/src/lib/screens/EffortRail.svelte     |  54 ------
 .../frontend/src/lib/screens/EffortRow.svelte      |  12 ++
 dashboard/frontend/src/lib/screens/Home.svelte     |  19 +-
 dashboard/frontend/src/lib/screens/Journal.svelte  |   3 +-
 dashboard/frontend/src/lib/screens/Overlay.svelte  |   5 +-
 .../frontend/src/lib/screens/ProductIndex.svelte   |  30 +++
 dashboard/frontend/src/lib/screens/Rail.svelte     |  94 +++++++++
 .../frontend/src/lib/screens/areaPage.test.ts      | 208 ++++++++++++++++++++
 dashboard/frontend/src/lib/screens/areas.test.ts   |  78 ++------
 .../src/lib/screens/breadcrumbRail.test.ts         | 193 ++++++++++++++++++
 .../frontend/src/lib/screens/closeFallback.test.ts | 133 +++++++++++++
 dashboard/frontend/src/lib/screens/dialogs.test.ts |   3 +-
 .../frontend/src/lib/screens/leaveRoute.test.ts    | 179 +++++++++++++++++
 .../frontend/src/lib/screens/productIndex.test.ts  | 215 +++++++++++++++++++++
 .../frontend/src/lib/screens/sidePanels.test.ts    | 149 ++++++++++++++
 .../frontend/src/lib/screens/startedChip.test.ts   | 158 +++++++++++++++
 dashboard/frontend/src/lib/state/areas.svelte.ts   |   9 +-
 dashboard/frontend/src/lib/state/areas.test.ts     | 168 ++++++++++++++++
 dashboard/frontend/src/lib/state/areas.ts          | 180 +++++++++++++++++
 .../frontend/src/lib/state/areasGuard.test.ts      |  61 ++++++
 dashboard/frontend/src/lib/state/keys.ts           |  27 +++
 dashboard/frontend/src/lib/state/overlay.svelte.ts |   4 +-
 dashboard/frontend/src/lib/state/polling.svelte.ts |  21 +-
 dashboard/frontend/src/main.test.ts                |  12 +-
 dashboard/frontend/src/milestoneNav.test.ts        |   6 +-
 dashboard/frontend/src/router.ts                   |  14 +-
 dashboard/frontend/src/side.test.ts                |  10 +-
 dashboard/frontend/src/sideRailCalm.test.ts        |  14 +-
 tests/dashboard/test_areas.py                      |  21 --
 tests/dashboard/test_areas_placement_edge.py       |  30 +++
 tests/dashboard/test_areas_promoted.py             |  90 +++++++++
 42 files changed, 2463 insertions(+), 288 deletions(-)
```
