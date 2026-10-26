---
{
  "id": "rec-e6781aab-2d6b-4f83-92e8-61cb6fb5084d",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "dashboard",
    "milestone": "web-calm",
    "ordinal": 33,
    "title": "Calm side rail"
  },
  "record_type": "plan:phase",
  "recorded_at": "2026-10-20T03:10:47+00:00",
  "relationships": {},
  "revision": "sha256:fda12dfafd50dc4130d92cc46c4afdc5d0d01ff7e8e8ec1b024cd9ed31a99bd0",
  "subject": "side-rail-calm"
}
---

## Problem

The home side rail lists journal entries in bulk, which overwhelms the screen when an effort has many entries.

## Approach

Remove journal rows from the home side rail. Keep Needs you and Backlog. For repair and evaluate efforts only, show a one-line open-count teaser that opens a dedicated journal hash screen (open then earlier, with search); rows open the record overlay. Decisions: `side-rail-journal-home`, `side-rail-journal-screen`, `side-rail-journal-kinds`.

## Exit criteria

- Home side rail has no journal entry rows; Needs you and Backlog remain.
- Repair/evaluate efforts show a journal teaser; deliver/incidental do not.
- Journal screen lists open then earlier, filters, and opens record overlays.
- UI tests and a manual look pass.

## Proof

kind: demo

A human opens the web dashboard, selects a repair or evaluate effort (or a seeded one), confirms the side rail has no journal list, opens Journal from the teaser, and filters entries.

## Landing

- branch: phase/side-rail-calm
- worktree: /home/andrewyin/orchestra/.worktrees/side-rail-calm
- base: main
- close: commit code on the phase branch; merge that branch into main; commit the store on the primary checkout
