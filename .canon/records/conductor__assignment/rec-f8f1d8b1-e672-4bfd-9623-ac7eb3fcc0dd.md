---
{
  "id": "rec-f8f1d8b1-e672-4bfd-9623-ac7eb3fcc0dd",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard",
    "executor": "subagent-e2e-area-seed",
    "work_item": "e2e-area-seed"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-30T08:28:14+00:00",
  "relationships": {},
  "revision": "sha256:9e58722c1f6679a74648580da46c08c75bdfb544faabffcad4538ec99e2a60ff",
  "subject": "e2e-area-seed"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/area-levels--e2e-area-seed` on task branch `task/area-levels/e2e-area-seed`.
Other tasks in this wave run in their own worktrees. Do not touch them.
Do not edit anything under `.canon/`.

### Work-item (quote)

## Description

R28: The Playwright test sees a seeded area card on `#/`.
R29: In the Playwright test, a click on a seeded area card opens `#/area/<subject>`.

## Approach

Edit `dashboard/frontend/e2e/serve.py`: add `composer` to the schemas in `canon init --schemas`, create one `composer:area` (subject `e2e-area`, payload `title`, body with a `## Scope` section as other areas have) and one `composer:placement` (subject = the seeded effort, payload `area`). Use `orchestra place` or `canon create` as the helper already does. Edit `e2e/app.spec.ts`: change the existing test to open `#/effort/e2e-alpha`, and add two tests. The test named `R28 the product index shows the seeded area card` goes to `/` and expects `[data-area-card="e2e-area"]` to be visible. The test named `R29 a click on the area card opens the area page` clicks that card and expects the URL hash to be `#/area/e2e-area`. Run `npm run e2e` from `dashboard/frontend`. Run `npm run lint` too.

### Requirements (quote by id)

R28: The Playwright test sees a seeded area card on `#/`.
R29: In the Playwright test, a click on a seeded area card opens `#/area/<subject>`.

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
