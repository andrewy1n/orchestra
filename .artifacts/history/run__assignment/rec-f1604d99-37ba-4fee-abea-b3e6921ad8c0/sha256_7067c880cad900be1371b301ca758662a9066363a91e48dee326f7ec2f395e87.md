---
{
  "id": "rec-f1604d99-37ba-4fee-abea-b3e6921ad8c0",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "packaging",
    "executor": "fix-opencode-agent",
    "work_item": "fix-opencode-shape"
  },
  "provenance": {
    "sources": [
      "fix-opencode-shape"
    ]
  },
  "record_type": "run:assignment",
  "recorded_at": "2026-10-19T02:20:17+00:00",
  "relationships": {},
  "revision": "sha256:7067c880cad900be1371b301ca758662a9066363a91e48dee326f7ec2f395e87",
  "subject": "fix-opencode-shape",
  "time": {
    "observed": "2026-10-19T02:20:17+00:00",
    "recorded": "2026-10-19T02:20:17+00:00"
  }
}
---

## Orientation

Territory: `installer/adapters/native.py`, `installer/agents.py`, `hosts/opencode/**`, `README.md`, `tests/test_installer.py`, `tests/test_agent_generation.py`, `tests/integration/test_temp_home_install.py`, and `tests/test_readme_matrix.py`. Do not edit `skills/**`, `orchestra/**`, `scripts/**`, `agents/**`, or the store.

Base: `483c621e1d813b9fe92d70b0c9c59a53d3080f79` on `phase/cross-harness-install`. OpenCode V2 docs confirm plugins auto-load from `.opencode/plugins/<file>` (project) and `~/.config/opencode/plugins/<file>` (global); root `plugin.js` is not discovered. Agents use `permissions:` plural; `permission` singular is legacy. `write`/`apply_patch` are gated by `edit`, which is already denied.

Operational: worktree `/home/andrewyin/orchestra/.worktrees/cross-harness-install`. Run pytest from the worktree. Do not call `adaptive-artifacts` or write `.artifacts/`. Commit with a `fix(hosts): ...` message whose body names `fix-opencode-shape`.

### Work-item (quote)



### Requirements (quote by id)

R12: Claude, Cursor, and OpenCode hook adapters are installed when supported, and installation succeeds when they are absent.

R13: The reviewer agent is generated per host from one canonical prompt and restriction set.

### Design / decisions (quote)

Design Invariants:
- Generated reference copies are byte-identical to their source.
- Skills call `orchestra`, `adaptive-artifacts`, and `aff` by name only.
- No adapter copies `.artifacts/`, `.worktrees/`, or dashboard state.
- The installer is idempotent: one registration per host per install scope.
- Store writes stay parent-only; subagents never write records.
- Existing checkout and plugin installs keep working.

Decision `npx-list-clause`: choice `remove-clause`. The specification no longer requires `npx skills add --list`; do not add a `--list` test.
