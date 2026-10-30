---
{
  "id": "rec-defb18e3-0282-4c2b-bc48-ca22bda5e9ac",
  "lifecycle_state": "done",
  "payload": {
    "effort": "ci",
    "ordinal": 1,
    "title": "v1 GitHub Actions workflow"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-29T07:06:27+00:00",
  "relationships": {},
  "revision": "sha256:3be61823ba1657597bccc629f8001430205cfd604e32afcb4f9eb388b94c31e2",
  "subject": "ci-workflow"
}
---

## Problem

No workflow runs the test suite, lint, store validation, or skill sync on push or pull request. Only `tuner-verdict.yml` runs, and it covers one fixture. A broken change reaches `main` without a signal.

## Approach

Chosen: one new workflow, `.github/workflows/ci.yml`, separate from `tuner-verdict.yml`. It runs on push to `main` and `phase/**`, on `pull_request`, and on `workflow_dispatch` (`ci-triggers`). Every job uses Python 3.10 (`ci-python-version`), sets `timeout-minutes`, and shares a `concurrency` group with `cancel-in-progress`.

Jobs, none depending on another: `checks` (skill sync, plugin names, `canon validate`, ruff); `test-canon`, `test-tuner` and `test-orchestra`, each a direct `uv run pytest -n auto` pass (`ci-test-job-layout`); `test-tmux`, serial with tmux installed; and a non-blocking `types` job with pinned mypy. The phase removes `scripts/test.sh` (`ci-test-job-layout`, superseded). `README.md` Testing lists the same four pytest commands for local runs. `CLAUDE.md` and `AGENTS.md` point to them. The phase suite command in `.canon/config.json` chains them.

Ruff is configured in `pyproject.toml` with rule set `F` only. The phase autofixes the F401, F541 and safe F-class errors and fixes the rest by hand (`ci-ruff-rules`). Current count: 37 errors, 34 with an autofix.

Execution starts after `wheel-contents` merged into `main`, so CI installs with `uv sync --locked --group dev` (`ci-after-wheel-contents`).

Task order: `ci-ruff-clean`, then `ci-workflow-file`, then `retire-test-sh`, then `verify-ci-workflow`. The workflow task adds `pyyaml` to the `dev` group and a `tests/test_ci_workflow.py` that parses `ci.yml` and asserts the structure per requirement.

Red-run proof: `act` is not installed. Acceptances for R23-R26 run each CI command against a deliberately broken temporary input and expect a non-zero exit. The workflow test also asserts no blocking job sets `continue-on-error` or `|| true`. The observed red runs on GitHub stay in `## Proof` as an optional human step.

## Exit criteria

- The workflow runs on a pull request and every blocking job passes (observed GitHub Actions run on the phase branch).
- A deliberate failure in each blocking job (test, ruff, `canon validate`, skill drift) turns the run red (observed run or `act` dry run per job; local broken-input proxy per job).
- `ruff check` exits 0 on the repository (command).
- `scripts/test.sh` is removed, no tracked file references it, and the documented and configured test commands pass (command).
- Every acceptance passes.

## Proof

kind: mixed. A human reads the green GitHub Actions run on the phase branch pull request, and the local `ruff check` output and the four pytest passes. The red-run proxies are commands.

## Session shape

more than one. The work finishes in one sitting up to the push. The green run needs a human push.

Human stops:
- Push `phase/ci-workflow` and open the pull request.
- Approve the `.canon/config.json` suite command change at plan review.
- Read the green Actions run (R27).
- Optional: push throwaway branches with a deliberate failure to see the red runs.

Collision notes: the ruff autofix touches about 30 files that in-flight phases (`shared-helpers`, `evidence-authority`, `standalone-aff`) may also edit. Run the autofix in the first task. Merge `main` into the phase branch before the final merge. `pyproject.toml` and `uv.lock` are also touched by `mypy-gate` and `wheel-smoke`, which run after this phase.

## Landing

- Branch: `phase/ci-workflow`
- Worktree: `/home/andrewyin/orchestra/.worktrees/ci-workflow`
- Base: `main`
- Close actions: commit code on the phase branch, merge the phase branch into `main`, commit the store on the primary checkout.
- Push: human stop only.
