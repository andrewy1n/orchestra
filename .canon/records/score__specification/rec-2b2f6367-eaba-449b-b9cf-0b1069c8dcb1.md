---
{
  "id": "rec-2b2f6367-eaba-449b-b9cf-0b1069c8dcb1",
  "lifecycle_state": "active",
  "payload": {
    "effort": "composer",
    "phase": "engage-from-idea",
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
      "R12"
    ],
    "weight": "full"
  },
  "record_type": "score:specification",
  "recorded_at": "2026-10-28T02:05:27+00:00",
  "relationships": {},
  "revision": "sha256:39ea80de84af6bad2a433e42dda93cc2b27b7113532d6ac3a43e006d85c7fb4b",
  "subject": "engage-from-idea"
}
---

## Requirements

R1: `engage` accepts the subject of an open `composer:idea` as the ask.
R2: `engage` lists open ideas from `orchestra view roadmap` when the user asks to start from an idea and names none.
R3: `engage` reads the named idea with `canon list --type composer:idea --subject <subject> --exact-subject`.
R4: `engage` refuses an idea whose status is not `open`.
R5: `engage` takes the idea's effort as the focus when the idea has an effort.
R6: `engage` routes an idea without an effort to `init` for a new effort.
R7: The routing line carries `idea: <subject> | none`.
R8: `init` supersedes the idea to `promoted` with the new effort after it creates the effort.
R9: `settle-phase` supersedes the idea to `promoted` with the effort and the new phase after it creates the phase.
R10: An idea stays `open` when the user stops before an effort or phase exists.
R11: The `engage` description names a triaged idea as an input.
R12: Skill contract tests accept every `canon` invocation in `engage`, `init` and `settle-phase`.

## Acceptance criteria

- R1 to R7, R10, R11: text checks in `tests/test_assess_routing.py` over the new `engage` text, and the skill contract extraction.
- R8, R9: text checks in the `init` and `settle-phase` skill tests, and the skill contract extraction.
- R12: the existing skill contract tests run over all three skills.

## Constraints

- `engage` stays a router. It writes no goal, phase, specification or work-item.
- The promote write follows the record it needs: refs point at records that exist when the supersede runs.
- The old promote bullet from phase `backlog-to-idea` becomes this path; `engage` keeps one promote flow.
- No schema version changes.

## Non-goals

- A command that runs the engage flow. Engage is a skill.
- Ranking ideas or choosing the next one for the user.
- Changing triage. Phase `idea-triage` owns it.
- Starting from an idea in another repository.

## Invariants

- At most one idea is promoted per `engage` run.
- A promoted idea carries the effort it became; the phase ref is set when a phase exists.
- Park and dismiss behave as phase `backlog-to-idea` left them.

## Assumptions

- Phases `backlog-to-idea` and `idea-triage` merge first. Both edit or rely on the `engage` text and on `orchestra view roadmap`.
- `engage` starts from any open idea, triaged or not. An untriaged idea still works; triage only adds an area.
- `init` and `settle-phase` already run in the same chat after `engage`, so the idea subject travels in the routing line and the chat context.
