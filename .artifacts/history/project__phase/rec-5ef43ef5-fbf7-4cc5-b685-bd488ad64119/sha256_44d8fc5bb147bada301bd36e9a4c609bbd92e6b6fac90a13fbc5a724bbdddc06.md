---
{
  "base_kind": "phase",
  "id": "rec-5ef43ef5-fbf7-4cc5-b685-bd488ad64119",
  "identity": "unknown",
  "lifecycle_state": "in_progress",
  "payload": {
    "effort": "packaging",
    "ordinal": 5,
    "title": "Package layout + uv tool install (PyPI later)"
  },
  "record_type": "project:phase",
  "recorded_at": "2026-10-15T20:57:29+00:00",
  "relationships": {},
  "revision": "sha256:44d8fc5bb147bada301bd36e9a4c609bbd92e6b6fac90a13fbc5a724bbdddc06",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "pyproject-pypi"
}
---

## Problem

Neither adaptive-artifacts nor affidavit ships a pyproject.toml. Install
is plugin checkout + PATH symlinks. `uv tool install git+…@tag` needs a
proper AA package layout first; PyPI waits until the format settles and
outsiders use it.

## Approach

AA-first git+ tool install (`packaging-scope-aa-first`). Restructure
adaptive-artifacts into an installable package with `pyproject.toml` and
an `adaptive-artifacts` entry point; keep `bin/adaptive-artifacts` and
`tools/artifacts.py` as thin shims (`aa-checkout-shims`) so plugin
installs and affidavit's `ADAPTIVE_ARTIFACTS_ROOT` discovery keep
working. Affidavit changes are README-only for the new install path. Do
not publish to PyPI (`pypi-publish-deferred`). AA code changes follow
the adaptive-artifacts extension gate.

Session shape: **more than one** sitting (AA restructure plus human
approval of the extension amendment before merge).

Human stops:
- Approve the adaptive-artifacts packaging amendment in that repo's
  store before AA code merges.
- Confirm Landing closes (affidavit docs on phase branch → merge to
  `main`; store commit on primary checkout). AA packaging commits land
  in the adaptive-artifacts repo under its own approval, not this
  worktree.
- Push only if requested.

Collision notes:
- Wave 1 runs in parallel: AA store amendment (adaptive-artifacts
  `.artifacts/`) and affidavit README (this repo). No shared files.
- Waves 2–3 are sequential in `~/adaptive-artifacts` only
  (`pyproject.toml`, `src/adaptive_artifacts/`, `bin/`, `tools/`).
- Affidavit product code and plugin manifests are untouched.

## Exit criteria

- `uv tool install` from the AA git URL yields a working
  `adaptive-artifacts` CLI (`--help` plus one store-touching command on
  a temp store) without a sibling checkout — verified manually or by an
  integration script in the AA repo.
- Plugin `bin/adaptive-artifacts` and checkout `tools/artifacts.py`
  still run the CLI against a temp store.
- Affidavit README documents git+ install and states PyPI is deferred;
  no affidavit `pyproject.toml` added.
- AA packaging amendment is captured and approved in the
  adaptive-artifacts store before that repo merges.

## Landing

- branch: `phase/pyproject-pypi`
- worktree: `/home/andrewyin/affidavit--pyproject-pypi`
- base: `main`
- close: commit affidavit docs (and any affidavit-side notes) on the
  phase branch; merge that branch into `main`; then commit the store on
  the primary checkout. AA packaging commits land in the
  adaptive-artifacts repo under its own Landing/approval, not this
  worktree.
- human stops: approve the adaptive-artifacts extension change before AA
  merge; push only if requested.
