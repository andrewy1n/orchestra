---
{
  "id": "rec-7a4ba67b-0fec-4b0e-b5bc-bc90d105d258",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "add-test,keep-clause",
    "choice": "remove-clause",
    "effort": "packaging",
    "phase": "cross-harness-install"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-19T02:19:39+00:00",
  "relationships": {},
  "revision": "sha256:af181ecd65062d20251d30435e20e32e1e5e5eeb2a96200d1f314fd90d474328",
  "subject": "npx-list-clause",
  "time": {
    "as_of": "2026-10-19T02:19:39+00:00"
  }
}
---

## Context

The phase specification's exit criteria included "`npx skills add --list` resolves a generic profile (R11, R12)." The final re-review found no test, README text, or installer path exercising `--list`.

## Options

- Add a stubbed `--list` test that invokes the `skills` CLI's repository-discovery command.
- Remove the clause.

## Rationale

Remove the clause.

`skills add --list` is a discovery command ("List available skills in the repository without installing"), not the installer's delegate path. R11's actual requirement — delegate at least one non-native host to `npx skills add -a <profile>` and report the profile — remains covered by the stubbed installer and temporary-HOME tests. Keeping a discovery command in the phase exit criteria would test the upstream CLI, not this installer.

## Counter-argument

Adding the stub would preserve the literal specification and prove the upstream `skills` CLI still exposes repository discovery. But the installer never runs `--list`, so the test would assert a command this phase does not depend on; a future `skills` CLI change could fail the phase without changing the installer. Removing the clause keeps the acceptance tied to the installer's actual delegate path.

## Consequence

The specification now asks only that a temporary-HOME install for Claude and OpenCode loads the generated skill dirs. No installer behavior changes.
