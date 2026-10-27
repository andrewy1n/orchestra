---
{
  "id": "rec-cbdd05be-a310-47b3-be75-5ac1d2fb6a3a",
  "lifecycle_state": "done",
  "payload": {
    "effort": "dashboard",
    "milestone": "web-calm",
    "ordinal": 34,
    "title": "Deep links"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-20T04:43:57+00:00",
  "relationships": {},
  "revision": "sha256:e33bd80b58dd5138e9d1846c5d472732294a4707a04e7a8045ddb9353cc00e0d",
  "subject": "deep-links"
}
---

## Problem

Record ids and cross-references appear as plain text, so it is hard to see what they refer to or open them.

## Approach

Linkify known reference shapes in list meta and markdown: task, phase, requirement (with context), record (`rec-…`), and milestone. Prefer human title and type as the label; leave unresolved tokens plain. Decisions: `deep-links-surfaces`, `deep-links-labels`.

## Exit criteria

- Known references navigate to the matching overlay or milestone focus.
- Labels prefer title/type; unresolved stay plain.
- Unit/UI tests and a manual follow-the-link check pass.

## Proof

kind: demo

A human opens a detail view that cites another record or task and follows the link to the target overlay.

## Landing

- branch: phase/deep-links
- worktree: /home/andrewyin/orchestra/.worktrees/deep-links
- base: main
- close: commit code on the phase branch; merge that branch into main; commit the store on the primary checkout

## Run

- size: one sitting
- human stops: approve the plan review before any task starts; open the web dashboard and follow one linkified reference before the phase closes
- collision: resolve helper and wire both touch markdown/detail surfaces — keep sequential waves (helper then wire then verify)
