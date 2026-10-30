---
{
  "id": "rec-ad3cc99b-a3f1-4a16-bca9-2eac6f9f31e3",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard",
    "executor": "subagent-area-chip-started",
    "work_item": "area-chip-started"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-30T08:32:10+00:00",
  "relationships": {},
  "revision": "sha256:8d33021bcdf1d7b0f1726a9a8dd1805a05ef71a095430ec1806683700758b56f",
  "subject": "area-chip-started"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/area-levels--area-chip-started` on task branch `task/area-levels/area-chip-started`.
Other tasks in this wave run in their own worktrees. Do not touch them.
Do not edit anything under `.canon/`.

### Work-item (quote)

## Description

R12: The area page shows promoted ideas whose effort is placed in the area under a "Started as efforts" heading.
R13: Each line under "Started as efforts" links to its effort.
R19: The effort page shows an area chip that links to `#/area/<subject>` when the effort has an area.

## Approach

Tests: write the test file named below. Start every test name with the requirement id and a space, for example `R5 an area card shows the open idea count`. Write one test for each requirement and no other test name starts with an id. Run the test first and see it fail on an assertion, then implement. File: `dashboard/frontend/src/lib/screens/startedChip.test.ts`.

1. `src/lib/screens/Home.svelte`: beside the effort title, when the effort has an `area` that matches an area, render `<a class="area-chip" data-area-chip href={areaHref(area)}>` with the area title. Render nothing when the effort has no area.
2. `src/lib/screens/Area.svelte`: add a section headed `Started as efforts` (`data-area-started`) after `Ideas`. It lists the ideas of the area with status `promoted` and an `effort`, one line each. A line shows the idea text and links to `effortHref(effort)` (`data-started-effort`). Show the section only when there are such ideas. A promoted idea never appears in the `Ideas` or `Efforts` sections.

Run `npm run lint`, `npm run check` and `npm test` in `dashboard/frontend` before you finish. Do not add comments that explain a change.

### Requirements (quote by id)

R12: The area page shows promoted ideas whose effort is placed in the area under a "Started as efforts" heading.
R13: Each line under "Started as efforts" links to its effort.
R19: The effort page shows an area chip that links to `#/area/<subject>` when the effort has an area.

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
- area-join-client-side: Group efforts in the browser from the snapshot; the backend adds promoted ideas to the area of their effort's placement
- landing-product-index: #/ shows the product index, one card for each area; the effort Home moves to #/effort/<name>
