---
{
  "id": "rec-7c837a04-4ce2-4ce4-b991-daaf8dc6bf62",
  "lifecycle_state": "active",
  "payload": {
    "decisions": [
      "phase-page-main-pane",
      "leaf-views-stay-modals",
      "effort-tasks-move-to-phase"
    ],
    "effort": "dashboard",
    "phase": "phase-level"
  },
  "record_type": "score:design",
  "recorded_at": "2026-10-30T07:52:34+00:00",
  "relationships": {},
  "revision": "sha256:ae6c569051400ee17487774cccc1c01a6c00d0627530ad1089f8f02119e6bc8a",
  "subject": "phase-level"
}
---

## Architecture

- `overlay.svelte.ts` splits in two. A `PhaseState` loads `GET /api/phase` for the route and derives the chrome, task graph, task list, evidence board and sections. `OverlayState` keeps the leaf modals: task, requirement, needs, backlog and record.
- `detail.ts` no longer treats `phase` as a detail kind. `detailTarget` returns null for it, so no dialog mounts. The `#/phase/<effort>/<phase>[/tab/<tab>]` format stays.
- `PhasePage.svelte` replaces the body of `PhaseOverlay.svelte`. It renders the header, chips, next action, requirement buttons, tabs, task graph, status tabs, task list, evidence board and sections in the main pane.
- `Overlay.svelte` keeps the `Dialog` for the leaf kinds only. `App.svelte` mounts `PhasePage` for the `phase` route.
- `Home.svelte` drops the phase filter, the status tabs and the task table. Its phase rows become links to the phase page, each with a progress bar. Milestone groups stay.
- The `Breadcrumb` and `Rail` from phase `area-levels` gain the phase level. The rail lists the phases of the effort with the current one marked and older done phases folded.
- `polling.svelte.ts` loses the phase filter and the status tab state that only the effort page used.

## Interfaces

- Routes: `#/phase/<effort>/<phase>` and `#/phase/<effort>/<phase>/tab/<tab>` render the page. The task, requirement, needs, backlog and record routes still open modals.
- `PhaseState` exposes the view models that the overlay exposes today for the phase kind.
- Esc on the phase route opens `#/effort/<effort>`.

## Decisions

- `phase-page-main-pane`: the phase renders as a page in the main pane.
- `leaf-views-stay-modals`: the leaf views stay modals over the phase page.
- `effort-tasks-move-to-phase`: the task table and status tabs move from the effort page to the phase page.

## Invariants

- Hash routing only. One served document.
- The phase page writes nothing.
- The URL decides the selected phase.
- Existing deep links resolve.

## Assumptions

- Phase `area-levels` is merged and exports the breadcrumb and the rail.
- The existing view-model builders (`buildPhaseChrome`, `taskBoard`, `evidenceBoard`, `buildWaveGraph`, `detailView`) can be called outside a dialog.
- Task and requirement modals open from the phase route without a page reload.

## Tradeoffs

- The effort page loses its cross-phase task view.
- Splitting the overlay state is the largest change in this phase, and the tests that mount the overlay must change with it.
- The page needs the theme for the task graph, as the dialog gets it today.

## Risks

- `overlay.svelte.ts` mixes link context, phase tabs and leaf views, so the split can break a link. Mitigation: R25 and the existing overlay tests, and a task that moves the state before it moves the UI.
- Esc handling is shared by the dialog and the app key handler. Mitigation: R28 and a test for each.
- Removing `polling` phase state breaks tests that assume it. Mitigation: update them in the same task as the removal.
