---
{
  "id": "rec-fdd5adb6-a587-4ae4-a68c-8b156c338ec8",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard",
    "executor": "subagent-product-index",
    "work_item": "product-index"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-30T08:18:21+00:00",
  "relationships": {},
  "revision": "sha256:8a96138ac4fd31cffcbfddaddce3fb00dc5d8a3bd118bd86c41de2e8148348cc",
  "subject": "product-index"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/area-levels--product-index` on task branch `task/area-levels/product-index`.
Other tasks in this wave run in their own worktrees. Do not touch them.
Do not edit anything under `.canon/`.

### Work-item (quote)

## Description

R1: `#/` shows the product index with one card for each area.
R2: An area card shows the area title.
R3: An area card shows the first sentence of the area's scope.
R4: An area card shows the number of efforts in the area.
R5: An area card shows the number of open ideas in the area.
R6: An area card lists the names of the efforts in the area.
R7: An area card is one link to `#/area/<subject>`.
R8: Efforts with no area show under a "Not in an area" heading on the product index.
R30: An area card contains no button.

## Approach

Tests: write the test file named below. Start every test name with the requirement id and a space, for example `R5 an area card shows the open idea count`. Write one test for each requirement and no other test name starts with an id. Run the test first and see it fail on an assertion, then implement. File: `dashboard/frontend/src/lib/screens/productIndex.test.ts`.

1. New `src/lib/screens/AreaCard.svelte`: one `<a class="area-card" data-area-card={subject} href={areaHref(subject)}>` that holds everything. No `<button>` inside. It shows the title, the first sentence of the scope (strip the markdown; take text up to the first `.`), the effort count, the open idea count and the effort names (`areaRollup`).
2. New `src/lib/screens/ProductIndex.svelte` with `data-product-index`: one `AreaCard` for each group of `groupByArea`. Efforts in `unplaced` show under a "Not in an area" heading, each as a link to `effortHref`. Show the unplaced group only when it holds efforts.
3. `src/App.svelte`: the `home` route renders `ProductIndex`. Other routes keep their current behavior, so `#/phase/...`, `#/task/...` and the others still render the effort Home behind the overlay.
4. `src/lib/screens/Home.svelte`: remove the `Areas` section (`data-areas`). The index replaces it.
5. Many existing tests mount the app at the empty hash and expect an effort Home. Change those mounts to `#/effort/<name>`. Do not change `src/deepLinks.test.ts`, `src/detail.test.ts`, `src/detailNav.test.ts` or `src/lib/screens/dialogs.test.ts` (R27); if one of them fails, stop and report it in the evidence block. Rewrite the Home-area tests in `src/lib/screens/areas.test.ts` (R6 `data-areas`) so they no longer expect the Areas block. Leave the area screen tests (R7 to R10) as they are; the `area-page` task rewrites them.
6. Add a small CSS block in `src/app.css` for the card grid and card. Use the existing CSS variables.

Run `npm run lint`, `npm run check` and `npm test` in `dashboard/frontend` before you finish. Do not add comments that explain a change.

### Requirements (quote by id)

R1: `#/` shows the product index with one card for each area.
R2: An area card shows the area title.
R3: An area card shows the first sentence of the area's scope.
R4: An area card shows the number of efforts in the area.
R5: An area card shows the number of open ideas in the area.
R6: An area card lists the names of the efforts in the area.
R7: An area card is one link to `#/area/<subject>`.
R8: Efforts with no area show under a "Not in an area" heading on the product index.
R30: An area card contains no button.

### Design / decisions (quote)

Invariants:
- Hash routing only. One served document.
- The product index and the area page write nothing.
- An idea never renders among the efforts.
- The URL decides the selected effort.

Assumptions:
- Phase `effort-area-link` is merged, so `area` is on every snapshot effort.
- The Home screen needs no change other than the chip.
- The Playwright seed store can hold an area and a placement.

Decisions:
- landing-product-index: #/ shows the product index, one card for each area; the effort Home moves to #/effort/<name>
- area-join-client-side: Group efforts in the browser from the snapshot; the backend adds promoted ideas to the area of their effort's placement
