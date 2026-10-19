---
{
  "base_kind": "phase",
  "id": "rec-85f75fda-1a30-4145-9cf0-2d4e1ed0ecd1",
  "identity": "unknown",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "workflow-loop",
    "ordinal": 13,
    "title": "Check runner: machine-produced check-runs"
  },
  "record_type": "project:phase",
  "recorded_at": "2026-10-10T21:51:58+00:00",
  "relationships": {},
  "revision": "sha256:a8d8217c58b063ab8eccaa870cae1d5c046a94223db3bf7d37be3ddefb3bfc1a",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "check-runner"
}
---

## Problem

A `project:check-run` is today a claim an agent types. Nothing runs `acceptance.verify_command`, so pass/fail, revision, and method can be invented or malformed. Dogfood evidence: most passing check-runs carry `revision: dirty`, and free-text `result`/`method` values have gotten through. Related work (red-first, tiered verification, phase-end reviewer) needs a trustworthy runner first.

## Approach

Decisions: se-workflow-cli, check-run-authority, dirty-pass-policy, check-run-enums, task-commit-evidence. Structured work: specification and design `check-runner`.

Ship a `se-workflow` CLI shell in this plugin with a real `check` subcommand and room for later commands. `se-workflow check` runs `verify_command` for `tdd`/`check`, writes the check-run through `adaptive-artifacts`, and derives `result` from the exit outcome with runner metadata. Hard authority: agents do not invent binary check-runs; they write assessments. Dirty `pass` is refused by default (`--allow-dirty` → `dirty` + `diff_sha256`); `fail` may be dirty. Contract enums for `result` and `method`. `execute-phase` commits per task so passes have a SHA. Manual stays human sign-off. No adaptive-artifacts extension in this phase.

## Exit criteria

- `se-workflow check` produces pass/fail/blocked check-runs with revision and runner fields for a throwaway store (integration test through the CLI).
- Dirty `pass` refused without override; override records `diff_sha256`.
- Contract rejects illegal `result`/`method`; self-consistency / dedicated tests pass.
- verify-work and close_batch (or documented successor) use CLI-produced check-runs for `tdd`/`check`; skill-contract tests pass.
- execute-phase requires per-task commit; its tests cover that rule.
