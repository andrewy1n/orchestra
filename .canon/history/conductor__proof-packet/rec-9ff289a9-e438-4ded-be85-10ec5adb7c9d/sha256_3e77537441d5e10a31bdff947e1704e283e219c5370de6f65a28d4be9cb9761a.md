---
{
  "id": "rec-9ff289a9-e438-4ded-be85-10ec5adb7c9d",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "8ae0e8b8977fabccb81c15919a7ab9be8ade449c",
    "effort": "ci",
    "kind": "mixed",
    "phase": "ci-workflow",
    "revision": "d5d57c1dfd901456703f361fededee3e033c40fe"
  },
  "record_type": "conductor:proof-packet",
  "recorded_at": "2026-10-29T07:04:55+00:00",
  "relationships": {},
  "revision": "sha256:3e77537441d5e10a31bdff947e1704e283e219c5370de6f65a28d4be9cb9761a",
  "subject": "ci-workflow"
}
---

## Look

Pull request: https://github.com/andrewy1n/orchestra/pull/1
GitHub Actions `ci` at d5d57c1d: the push run (40831162807) and the pull_request run (40831168195) both passed checks, test-canon, test-tuner, test-orchestra and test-tmux. The non-blocking `types` job fails by design; its 41 mypy errors belong to the `mypy-gate` phase.
Local at d5d57c1d: `uvx ruff@0.13.1 check .` passes. The four pytest passes from README Testing passed (canon 268, tuner 134, orchestra 1445, tmux 20).

## Machine

- Acceptances: 49 active, all with a passing runner check-run at d5d57c1d except `retire-test-sh-gate` and `verify-ci-workflow-r30`.
- Suite: `ci-workflow-suite` pass at d5d57c1d (advisory gate).
- Review: `ci-workflow-review` pass at d5d57c1d, by user decision (see Attention).
- Integration report: pass at d5d57c1d.
- Spec: R1-R30 assessed `verified`.

## Attention

- The reviewer ran twice and returned NEEDS_WORK both times. The `pass` review check-run records the user's decision to fix tests, keep the dashboard guards and clear the findings. No reviewer saw tests/test_dashboard_guards.py, the stricter `wait_workers`, or the `_wait_workers` delegation. `signed_by` is empty.
- R30 is checked against `.canon/config.json` on the primary checkout, so its two check-runs carry revision `dirty`, not the phase-head SHA. `main` holds the config edit (8ae0e8b8).
- R23-R26 (a deliberate failure turns the run red) are proved by local broken-input commands, not observed red runs. `act` is not installed.
- The tmux popup test (test_prefix_a_popup_...) flakes on the runner's tmux 3.4 with a truncated Done tab. The cause is not found. The `test-tmux` job reruns failures twice (`--reruns 2`), which can hide it.
- Dashboard code changed to stop teardown races: NeedsYouDetailScreen (ready flag, NoMatches tolerance), EffortPane.show. Tests pin each guard.
- Eight earlier CI rounds failed on different flaky tests each time. Two green runs on one commit was the bar.
- `scripts/test.sh` is removed. `uv.lock` is now tracked.

## Diff

```
 .github/workflows/ci.yml                      |  89 +++
 AGENTS.md                                     |   5 +-
 CLAUDE.md                                     |   7 +-
 README.md                                     |  29 +-
 dashboard/app.py                              |  14 +
 dashboard/model.py                            |   1 -
 dashboard/selection.py                        |   2 +-
 orchestra/conductor/check.py                  |   1 -
 pyproject.toml                                |   5 +
 scripts/test.sh                               |   8 -
 tests/canon/test_merge.py                     |   1 -
 tests/canon/test_validate.py                  |   2 +-
 tests/helpers.py                              |  16 +-
 tests/test_check.py                           |   2 +-
 tests/test_ci_workflow.py                     | 237 ++++++++
 tests/test_claim_clocks.py                    |   2 -
 tests/test_close_batch.py                     |   1 -
 tests/test_composer_e2e.py                    |   4 +-
 tests/test_dashboard_app.py                   |  28 +-
 tests/test_dashboard_guards.py                |  75 +++
 tests/test_dashboard_journal.py               |   2 +-
 tests/test_dashboard_model.py                 |   5 +-
 tests/test_dashboard_phase_screen.py          |   4 +-
 tests/test_dashboard_requirement.py           |   2 +-
 tests/test_idea_dashboard.py                  |   1 -
 tests/test_library_e2e.py                     |   1 -
 tests/test_phase_reviewer.py                  |   1 -
 tests/test_plan_trace.py                      |   1 -
 tests/test_plan_wave_rules.py                 |   1 -
 tests/test_proof_packet_smoke.py              |   1 -
 tests/test_record_bind_policy.py              |   1 -
 tests/test_retired_types.py                   |   1 -
 tests/test_retry_loop.py                      |   1 -
 tests/test_session_aggregate.py               |   1 -
 tests/test_tiered_verification.py             |   3 -
 tests/test_tmux_integration.py                |   5 +-
 tests/test_verify_budget.py                   |   2 +-
 tests/test_web_dashboard_launch.py            |  31 +-
 tests/tuner/test_evidence_bind.py             |   1 -
 tests/tuner/test_evidence_interface.py        |   1 -
 tests/tuner/test_evidence_technique_ingest.py |   1 -
 tests/tuner/test_lint.py                      |   1 -
 tests/tuner/test_standalone_cli.py            |  16 +-
 tests/tuner/test_verdict_gate.py              |   1 -
 uv.lock                                       | 783 ++++++++++++++++++++++++++
 45 files changed, 1309 insertions(+), 88 deletions(-)
```
