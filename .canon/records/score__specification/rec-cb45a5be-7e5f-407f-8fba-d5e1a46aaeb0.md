---
{
  "id": "rec-cb45a5be-7e5f-407f-8fba-d5e1a46aaeb0",
  "lifecycle_state": "active",
  "payload": {
    "effort": "composer",
    "phase": "idea-triage",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6",
      "R7",
      "R8",
      "R9",
      "R10",
      "R11",
      "R12",
      "R13",
      "R14",
      "R15",
      "R16",
      "R17",
      "R18",
      "R19",
      "R20"
    ],
    "weight": "full"
  },
  "record_type": "score:specification",
  "recorded_at": "2026-10-28T02:04:49+00:00",
  "relationships": {},
  "revision": "sha256:3a51b895f06639583ebe9d7fe7625e4c8c99167fc748ff1555193b4b1f0f95cf",
  "subject": "idea-triage"
}
---

## Requirements

R1: `orchestra idea "<title>"` creates an open `composer:idea` whose subject is the slugified title.
R2: `orchestra idea` writes the title as the first line of the idea body.
R3: `orchestra idea --area <slug>` sets the idea's area.
R4: `orchestra idea --effort <slug>` sets the idea's effort.
R5: `orchestra idea --source <text>` sets the idea's source.
R6: `orchestra idea --body-file <path>` appends the file text to the idea body below the title.
R7: `orchestra idea` exits non-zero and writes nothing when an idea with the derived subject exists.
R8: `orchestra idea` exits non-zero and writes nothing when `--area` names no active `composer:area`.
R9: `orchestra idea` exits non-zero and writes nothing when `--effort` names no active `score:effort`.
R10: `orchestra view roadmap` groups open and promoted `composer:idea` records by area.
R11: `orchestra view roadmap` lists ideas without an area under a group named `untriaged`.
R12: `orchestra view roadmap` hides dismissed ideas.
R13: `orchestra view roadmap` shows the effort of each promoted idea.
R14: `orchestra view roadmap --effort <slug>` lists only ideas with that effort.
R15: The `triage-ideas` skill lists open ideas that have no area.
R16: The `triage-ideas` skill assigns an area with `canon supersede --type composer:idea`.
R17: The `triage-ideas` skill creates a `composer:area` with `canon create --type composer:area` when no area fits.
R18: The `triage-ideas` skill dismisses an idea with `canon supersede --type composer:idea` to status `dismissed`.
R19: The `triage-ideas` skill does not set status `promoted`; it names `engage` for that.
R20: `orchestra idea` and `orchestra view roadmap` run through the installed entry point from an unrelated directory.

## Acceptance criteria

- R1 to R9: unit tests over `orchestra.composer` capture logic and CLI tests against a temporary store.
- R10 to R14: `tests/test_views.py` builds areas and ideas in each state and compares the rendered markdown.
- R15 to R19: the skill contract test accepts every `canon` invocation in the new skill and checks its steps by text.
- R20: an integration test in `tests/test_cli_packaging.py` style runs both commands from an installed prefix.

## Constraints

- composer imports only canon and score. The capture logic lives in `orchestra/composer/`. CLI wiring and the roadmap view live in the top-level modules.
- The view engine change is small: one optional group-default setting on `View`. Existing views render unchanged.
- The new skill follows the structure of `settle-phase`: parent session writes, no subagents write.
- No schema version changes.

## Non-goals

- `engage` starting an effort from an idea. That is phase `engage-from-idea`.
- Ordering or lanes on the roadmap. Areas group ideas; nothing ranks them.
- Editing an idea's title or body after capture.
- A dashboard panel for effortless ideas.

## Invariants

- `orchestra idea` writes one record or none.
- Dismissed ideas stay in the store. Only the roadmap hides them.
- The roadmap view is derived. No command edits view output.

## Assumptions

- Phase `backlog-to-idea` merges first, so `composer:idea` records and the dashboard panel are in their final shape.
- A `composer:idea` area value is the subject slug of a `composer:area`, as `effort` is the subject slug of a `score:effort`.
- The title slug uses lowercase letters, digits and single hyphens, and is capped at a fixed length set at plan-phase.
