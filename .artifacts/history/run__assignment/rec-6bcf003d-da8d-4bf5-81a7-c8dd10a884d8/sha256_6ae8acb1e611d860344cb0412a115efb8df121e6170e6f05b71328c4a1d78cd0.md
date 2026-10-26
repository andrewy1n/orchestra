---
{
  "id": "rec-6bcf003d-da8d-4bf5-81a7-c8dd10a884d8",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "packaging",
    "executor": "portable-refs-agent",
    "work_item": "portable-skill-refs"
  },
  "provenance": {
    "sources": [
      "portable-skill-refs"
    ]
  },
  "record_type": "run:assignment",
  "recorded_at": "2026-10-18T22:38:59+00:00",
  "relationships": {},
  "revision": "sha256:6ae8acb1e611d860344cb0412a115efb8df121e6170e6f05b71328c4a1d78cd0",
  "subject": "portable-skill-refs",
  "time": {
    "observed": "2026-10-18T22:38:59+00:00",
    "recorded": "2026-10-18T22:38:59+00:00"
  }
}
---

## Orientation

Territory: `shared/`, `scripts/build_skills.py`, every `skills/<name>/SKILL.md` and `skills/<name>/references/`, and `tests/test_skill_portability.py`. Do not edit `pyproject.toml`, `src/orchestra/**`, `installer/**`, `hosts/**`, or `tests/test_cli_packaging.py`; `cli-package` owns those in the same wave.

Concurrency: `cli-package` edits the runtime packaging in parallel. Keep all writes under `/home/andrewyin/orchestra/.worktrees/cross-harness-install`.

Operational: run pytest from the worktree. If a test needs the runtime, set `PYTHONPATH` to the worktree or call `bin/orchestra`. Do not write `.artifacts/`; return evidence and let the parent write the store.

### Work-item (quote)

## Description

R1: Every advertised skill directory contains all files its instructions reference; no referenced path leaves the directory.
R2: The shared `ensure-store.md` and `kinds-and-focus.md` text is generated into each skill's `references/` from one source.
R3: A drift check fails when a generated `references/` copy differs from its source.
R4: Every `SKILL.md` passes Agent Skills frontmatter validation: `name` equals its directory and `description` is non-empty.
R6: No skill body names a checkout path or `<plugin>` root for a runtime call.

## Approach

Create `shared/ensure-store.md` and `shared/kinds-and-focus.md` from the current root docs. Add `scripts/build_skills.py` to sync them into `skills/<name>/references/` and to run a `--check` drift comparison. Rewrite every advertised `SKILL.md` to use `references/...`; replace `<plugin>/...` and `~/affidavit/bin/aff` with the named commands `orchestra`, `aff`, and `adaptive-artifacts`. Add `tests/test_skill_portability.py` proving R1-R4 and R6, including a planted `../` reference that must fail. Keep `shared/` as the only source and the generated `skills/` tree as the install payload.

### Requirements (quote by id)

R1: Every advertised skill directory contains all files its instructions reference; no referenced path leaves the directory.
R2: The shared `ensure-store.md` and `kinds-and-focus.md` text is generated into each skill's `references/` from one source.
R3: A drift check fails when a generated `references/` copy differs from its source.
R4: Every `SKILL.md` passes Agent Skills frontmatter validation: `name` equals its directory and `description` is non-empty.
R6: No skill body names a checkout path or `<plugin>` root for a runtime call.

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

Decision `portable-skill-references`: choice `generate-per-skill-references`.
