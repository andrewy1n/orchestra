---
{
  "id": "rec-defb18e3-0282-4c2b-bc48-ca22bda5e9ac",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "ci",
    "ordinal": 1,
    "title": "v1 GitHub Actions workflow"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-28T07:52:02+00:00",
  "relationships": {},
  "revision": "sha256:c9393625bd751dd8bcf9f2f537363d407fa95dc95ad48b88d0cb8ce4b7127b04",
  "subject": "ci-workflow"
}
---

## Problem

No workflow runs the test suite, lint, store validation, or skill sync on push or pull request. Only `tuner-verdict.yml` runs, and it covers one fixture. A broken change reaches `main` without a signal.

## Approach

Add one GitHub Actions workflow on push and pull request, separate from `tuner-verdict.yml`. A `checks` job runs `scripts/build_skills.py --check`, `scripts/check_orchestra_plugin_names.py`, `canon validate`, and ruff with a narrow pinned rule set in `pyproject.toml`. Test jobs run the `scripts/test.sh` passes in parallel with `-n auto` and uv caching. A separate job installs tmux and runs the `tmux` marker serially. A `types` job runs mypy without blocking. The workflow sets `concurrency` with `cancel-in-progress` and a `timeout-minutes` on each job. Settle details at settle-phase.

## Exit criteria

- The workflow runs on a pull request and every blocking job passes (observed GitHub Actions run on the phase branch).
- A deliberate failure in each blocking job (test, ruff, `canon validate`, skill drift) turns the run red (observed run or `act` dry run per job).
- `scripts/test.sh` still passes locally (command).
