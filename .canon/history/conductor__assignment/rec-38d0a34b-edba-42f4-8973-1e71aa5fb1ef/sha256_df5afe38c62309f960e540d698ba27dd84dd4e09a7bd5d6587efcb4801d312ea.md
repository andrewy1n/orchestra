---
{
  "id": "rec-38d0a34b-edba-42f4-8973-1e71aa5fb1ef",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "library-boundary",
    "executor": "package-metadata",
    "work_item": "package-metadata"
  },
  "provenance": {
    "sources": [
      "package-metadata"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-22T06:57:31+00:00",
  "relationships": {},
  "revision": "sha256:df5afe38c62309f960e540d698ba27dd84dd4e09a7bd5d6587efcb4801d312ea",
  "subject": "package-metadata",
  "time": {
    "observed": "2026-10-22T06:57:31+00:00",
    "recorded": "2026-10-22T06:57:31+00:00"
  }
}
---

## Orientation

Wave 1. This task does not share files with `import-open` or `format-gate`. Orchestra edits stay in this worktree. The affidavit `pyproject.toml` is written in `/home/andrewyin/affidavit/.worktrees/declared-install`, which is the tree the R1 test reads. Do not edit the primary checkouts.

Write root: `/home/andrewyin/orchestra/.worktrees/declared-install--package-metadata` for orchestra. Affidavit metadata write root: `/home/andrewyin/affidavit/.worktrees/declared-install` on `phase/declared-install`.

### Work-item (quote)

## Description

R1: The affidavit package declares a dependency on adaptive-artifacts.
R2: The orchestra package declares a dependency on adaptive-artifacts.
R3: The orchestra package does not declare affidavit as a required dependency.
R4: The orchestra `evidence` extra declares a dependency on affidavit.

## Approach

Add `pyproject.toml` at the affidavit repo root. `[project].dependencies` includes adaptive-artifacts as `adaptive-artifacts @ git+https://github.com/andrewy1n/adaptive-artifacts`. Use setuptools, `packages = ["affidavit"]`, and `aff = "affidavit.cli:main"`.

In orchestra `pyproject.toml`, declare that same adaptive-artifacts direct reference in `[project].dependencies`. Do not put affidavit in that list. Add `[project.optional-dependencies]` with `evidence = ["affidavit @ git+https://github.com/andrewy1n/affidavit"]`.

Leave the adaptive-artifacts `pyproject.toml` as the package named adaptive-artifacts, with no dependency on orchestra or affidavit. The declaration test reads `~/affidavit/pyproject.toml`, `~/adaptive-artifacts/pyproject.toml`, and this repo's `pyproject.toml`.

### Requirements (quote by id)

R1: The affidavit package declares a dependency on adaptive-artifacts.
R2: The orchestra package declares a dependency on adaptive-artifacts.
R3: The orchestra package does not declare affidavit as a required dependency.
R4: The orchestra `evidence` extra declares a dependency on affidavit.

### Design / decisions (quote)

## Invariants

Importable adaptive-artifacts after a normal install. No affidavit unless the extra was requested. Unknown contract format fails open.

## Assumptions

Plugin hosts can run a package installer. `uv tool install` honors the dependency and the extra.

install-graph: dependencies-and-path

## Rationale

The user chose dependencies and PATH. Affidavit depends on adaptive-artifacts. Orchestra depends on adaptive-artifacts, and the `evidence` extra depends on affidavit. Plugin install installs those packages. The old search through plugin roots, sibling checkouts, and `ADAPTIVE_ARTIFACTS_BIN` goes away. `open_store` rejects a contract format this build does not list.

version-check: dependency-specifier-and-contract-format

## Rationale

Once orchestra depends on adaptive-artifacts, the installer rejects a combination that cannot import. The check that still belongs at runtime is the contract format, which fails when the store was written by a format this build does not understand. That replaces the parked `version-compat-check` item, which compared `--version` strings across a process boundary.

dependency-direction: affidavit-on-aa-orchestra-on-both

## Rationale

Affidavit depends on adaptive-artifacts. Orchestra depends on adaptive-artifacts always, and on affidavit only when close needs evidence. That import stays inside the close command. Affidavit does not import orchestra.

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done.

- `tests/test_declared_install_metadata.py`
