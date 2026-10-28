---
{
  "id": "rec-fb8530cb-3fe9-4b7a-95e4-dcfb27d15e81",
  "lifecycle_state": "done",
  "payload": {
    "effort": "composer",
    "ordinal": 3,
    "title": "Idea command, triage skill and roadmap view"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-28T07:38:40+00:00",
  "relationships": {},
  "revision": "sha256:0e8043c59bbd78e922fe0f7db6f201014a33df09f53557a5ecdda45a09226d04",
  "subject": "idea-triage"
}
---

## Problem

There is no command to capture an idea, no skill to triage ideas, and no view of the roadmap.

## Approach

Chosen: `orchestra idea "<title>"` with a derived slug (`idea-command-shape`). Capture logic lives in `orchestra/composer/idea.py`; the CLI wiring and the roadmap view live at top level. `orchestra view roadmap` is a normal view grouped by area with an `untriaged` default group (`roadmap-group-default`). A `triage-ideas` skill assigns an area, creates an area, or dismisses; promotion belongs to `engage-from-idea`.

Session shape: one sitting. Waves: `idea-capture`, `roadmap-view` and `triage-ideas-skill` (subagent, Cursor workers); then `idea-packaging-check`; then `verify-idea-triage`.

Human stops: plan review (approved in the user's auto-execute request). Push is not a stop; this phase does not push.

Collision notes:
- The three wave-1 tasks touch disjoint files: `orchestra/composer/idea.py` and `orchestra/cli.py`; `orchestra/views.py`, `orchestra/view_cli.py` and `tests/test_views.py`; `skills/triage-ideas/`, `README.md` and a new skill test.
- Frozen oracles: `tests/test_idea_command.py` and `tests/test_roadmap_view.py`.
- The suite gate is advisory (set by the user in `.canon/config.json`).

## Exit criteria

- Every acceptance passes.
- An integration check runs `orchestra idea` and `orchestra view roadmap` through the installed entry point.
- The skill contract tests accept every `canon` invocation in `triage-ideas`.
- `scripts/test.sh` passes.

## Proof

kind: mixed. A human reads the check-runs for the capture, view and skill-contract tests, and the rendered roadmap for the live store.

## Landing

- Branch: `phase/idea-triage`
- Worktree: `/home/andrewyin/orchestra/.worktrees/idea-triage`
- Base: `main`
- Close actions: commit code on the phase branch; merge the branch into `main`; commit the store on the primary checkout.
- Push: not part of this phase.
