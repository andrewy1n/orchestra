---
{
  "id": "rec-aa430efd-0a8d-47a6-9a6e-80297fcbdfec",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "packaging",
    "executor": "cli-package-agent",
    "work_item": "cli-package"
  },
  "provenance": {
    "sources": [
      "cli-package"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T22:38:59+00:00",
  "relationships": {},
  "revision": "sha256:5dadb00f0f19d8a2b542f02d48d616d43cfc09581f9dae1460eeb0312e9cb02d",
  "subject": "cli-package",
  "time": {
    "observed": "2026-10-18T22:38:59+00:00",
    "recorded": "2026-10-18T22:38:59+00:00"
  }
}
---

## Orientation

Territory: `pyproject.toml`, `src/orchestra/**`, `bin/orchestra`, `tests/test_cli_packaging.py`, and `tests/integration/test_cli_on_path.py`. Do not edit `skills/**`, `shared/**`, `scripts/build_skills.py`, `installer/**`, `hosts/**`, or `tests/test_skill_portability.py`; `portable-skill-refs` owns those in the same wave.

Concurrency: `portable-skill-refs` edits the skill tree in parallel. Keep all writes under `/home/andrewyin/orchestra/.worktrees/cross-harness-install`.

Operational: the current package is importable from the worktree root (`PYTHONPATH=.`). `bin/orchestra` is the existing entry point. Do not write `.artifacts/`; return evidence and let the parent write the store.

### Work-item (quote)

## Description

R5: `orchestra` installs as a console script and runs from PATH in an unrelated working directory.
R7: `orchestra` provides `contract`, `project-field`, and `sessions` subcommands covering what skills currently reach for by file path.

## Approach

Add `pyproject.toml` with the `orchestra` package and `[project.scripts] orchestra = "orchestra.cli:main"`; include `contract/project-design.json` as package data. Add `contract`, `project-field`, and `sessions` subcommands to `orchestra/cli.py`, delegating to the existing modules and scripts. Keep `bin/orchestra` as a shim that resolves the checkout. Add `tests/test_cli_packaging.py` that installs into a temporary prefix and runs each subcommand from an unrelated cwd. Add `tests/integration/test_cli_on_path.py` that runs `orchestra check --help` through the installed entry point.

### Requirements (quote by id)

R5: `orchestra` installs as a console script and runs from PATH in an unrelated working directory.
R7: `orchestra` provides `contract`, `project-field`, and `sessions` subcommands covering what skills currently reach for by file path.

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
