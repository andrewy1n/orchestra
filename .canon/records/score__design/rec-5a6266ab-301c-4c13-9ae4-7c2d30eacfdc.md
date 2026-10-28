---
{
  "id": "rec-5a6266ab-301c-4c13-9ae4-7c2d30eacfdc",
  "lifecycle_state": "active",
  "payload": {
    "decisions": [
      "cli-verbs-stay-skills"
    ],
    "effort": "package-layout",
    "phase": "cli-verbs"
  },
  "record_type": "score:design",
  "recorded_at": "2026-10-28T06:58:53+00:00",
  "relationships": {},
  "revision": "sha256:4ad804a9efccad8dce56f1616b79ecfa304dea3b8eb5953955db257e1b7ae090",
  "subject": "cli-verbs"
}
---

## Architecture

No new subcommands. `orchestra view plan` remains the plan view. `plan-phase` and `execute-phase` remain the skills. The README skills list and CLI section are the places a reader checks. This phase changes the README only if one of those lines is missing or if it documents `orchestra plan` or `orchestra run` as a command.

## Interfaces

- `orchestra --help`.
- `orchestra view plan`.
- README sections "Skills in this pack" and "CLI".

## Decisions

- `cli-verbs-stay-skills`: `plan` and `run` stay skills. `orchestra idea` stays in the composer effort.

## Invariants

- The CLI does not grow a `plan` or `run` subcommand in this effort.

## Assumptions

- The current README already lists the skills and `view`. The phase confirms that and edits only a contradiction.

## Tradeoffs

- The monorepo plan's verb table stays stale on those two names. The README is the list that matches the CLI.

## Risks

- A later reader treats the monorepo plan as the command list and adds the verbs anyway. The decision is the record that closes that reading.
