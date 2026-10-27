---
{
  "id": "rec-a38aa1ad-2eab-4685-ba8f-dc6050a5f184",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "packaging",
    "executor": "fix-reviewer-agent",
    "work_item": "fix-reviewer-selfcontainment"
  },
  "provenance": {
    "sources": [
      "fix-reviewer-selfcontainment"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T23:58:01+00:00",
  "relationships": {},
  "revision": "sha256:87f7c378e7476015d48a9f0b3210da800b3df7c39b7b3982e7f75c198540f072",
  "subject": "fix-reviewer-selfcontainment",
  "time": {
    "observed": "2026-10-18T23:58:01+00:00",
    "recorded": "2026-10-18T23:58:01+00:00"
  }
}
---

## Orientation

Territory: `skills/execute-phase/**`, `agents/**`, `scripts/build_skills.py`, `tests/test_skill_portability.py`, and `tests/test_agent_generation.py`. Do not edit `orchestra/**`, `installer/**`, `hosts/**`, `README.md`, `tests/test_cli_packaging.py`, or `tests/test_installer.py`.

Concurrency: `fix-cli-standalone` and `fix-docs-and-hooks` run in parallel and touch other paths. `fix-cli-runtime-surface` follows and will edit `skills/execute-phase/SKILL.md` and `tests/test_skill_portability.py` again, so leave a clear note about your changes.

Operational: worktree `/home/andrewyin/orchestra/.worktrees/cross-harness-install`. Run pytest from the worktree. Do not write `.artifacts/`; return evidence and let the parent write the store.

### Work-item (quote)



### Requirements (quote by id)

R1: Every advertised skill directory contains all files its instructions reference; no referenced path leaves the directory.
R13: The reviewer agent is generated per host from one canonical prompt and restriction set.

### Design / decisions (quote)

Design Invariants:
- Generated reference copies are byte-identical to their source.
- Skills call `orchestra`, `adaptive-artifacts`, and `aff` by name only.
- No adapter copies `.artifacts/`, `.worktrees/`, or dashboard state.
- The installer is idempotent: one registration per host per install scope.
- Store writes stay parent-only; subagents never write records.
- Existing checkout and plugin installs keep working.

Design Assumptions:
- `npx skills add` keeps its `-a <profile>` interface and profile ids.
- Hosts read `SKILL.md` from the paths in the provider matrix.
- `uv` is available wherever the CLI install is documented.
- OpenCode accepts a `skills` config source and `agents/*.md`.
- Claude and Cursor manifest schemas stay compatible.

Decision `reviewer-agent-generation`: choice `generate-per-host-frontmatter`.
