---
{
  "id": "rec-fb8530cb-3fe9-4b7a-95e4-dcfb27d15e81",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "composer",
    "ordinal": 3,
    "title": "Idea command, triage skill and roadmap view"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-28T02:04:50+00:00",
  "relationships": {},
  "revision": "sha256:9896b9da158b656f0f3c1e00cf82895c6db6c4c853a61981b65667c161a956df",
  "subject": "idea-triage"
}
---

## Problem

There is no command to capture an idea, no skill to triage ideas, and no view of the roadmap.

## Approach

Chosen: `orchestra idea "<title>"` with a derived slug (`idea-command-shape`). Capture logic lives in `orchestra/composer/`; the CLI wiring and the roadmap view live at top level. `orchestra view roadmap` is a normal view grouped by area with an `untriaged` default group (`roadmap-group-default`). A `triage-ideas` skill assigns an area, creates an area, or dismisses; promotion belongs to `engage-from-idea`. The phase starts after `backlog-to-idea` merges.

## Exit criteria

- Every acceptance passes.
- An integration check runs `orchestra idea` and `orchestra view roadmap` through the installed entry point.
- The skill contract tests accept every `canon` invocation in `triage-ideas`.
- `scripts/test.sh` passes.

## Proof

kind: mixed. A human reads the check-runs for the capture, view and skill-contract tests, and the rendered roadmap for a sample store.
