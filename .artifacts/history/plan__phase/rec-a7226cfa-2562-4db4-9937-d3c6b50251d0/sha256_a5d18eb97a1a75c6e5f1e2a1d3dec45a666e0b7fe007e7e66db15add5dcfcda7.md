---
{
  "id": "rec-a7226cfa-2562-4db4-9937-d3c6b50251d0",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "monorepo",
    "ordinal": 0,
    "title": "Prepare repos and backups"
  },
  "record_type": "plan:phase",
  "recorded_at": "2026-10-27T07:46:11+00:00",
  "relationships": {},
  "revision": "sha256:a5d18eb97a1a75c6e5f1e2a1d3dec45a666e0b7fe007e7e66db15add5dcfcda7",
  "subject": "monorepo-prepare"
}
---

## Problem

Open worktrees, a PyPI branch and dead stores block a clean move.

## Approach

Review the two dirty orchestra worktrees with the owner, drop affidavit phase/pyproject-pypi, remove merged worktrees, write verified git bundles, delete ~/aa-plugin-dogfood and ~/.artifacts.

## Exit criteria

Only primary checkouts remain and the three bundles verify.
