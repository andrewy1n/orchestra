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
  "recorded_at": "2026-10-28T08:03:42+00:00",
  "relationships": {},
  "revision": "sha256:20d2656f26e40894ff6af8073aa97736207e17aae34027788fb3a6708dacebd7",
  "subject": "ci-workflow"
}
---

## Problem

No workflow runs the test suite, lint, store validation, or skill sync on push or pull request. Only `tuner-verdict.yml` runs, and it covers one fixture. A broken change reaches `main` without a signal.

## Approach

Chosen: one new workflow, `.github/workflows/ci.yml`, separate from `tuner-verdict.yml`. It runs on push to `main` and `phase/**`, on `pull_request`, and on `workflow_dispatch` (`ci-triggers`). Every job uses Python 3.10 (`ci-python-version`), sets `timeout-minutes`, and shares a `concurrency` group with `cancel-in-progress`.

Jobs, none depending on another: `checks` (skill sync, plugin names, `canon validate`, ruff); `test-canon`, `test-tuner` and `test-orchestra`, each a direct `uv run pytest -n auto` pass (`ci-test-job-layout`); `test-tmux`, serial with tmux installed; and a non-blocking `types` job with pinned mypy. `scripts/test.sh` is unchanged.

Ruff is configured in `pyproject.toml` with rule set `F` only. The phase autofixes 33 errors and fixes 2 by hand (`ci-ruff-rules`).

Execution waits for `wheel-contents` to merge, so CI installs with `uv sync --locked --group dev` (`ci-after-wheel-contents`).

## Exit criteria

- The workflow runs on a pull request and every blocking job passes (observed GitHub Actions run on the phase branch).
- A deliberate failure in each blocking job (test, ruff, `canon validate`, skill drift) turns the run red (observed run or `act` dry run per job).
- `ruff check` exits 0 on the repository (command).
- `scripts/test.sh` still passes locally (command).
- Every acceptance passes.

## Proof

kind: mixed. A human reads the green GitHub Actions run on the phase branch pull request, the red runs for each deliberate failure, and the local `ruff check` and `scripts/test.sh` output.
