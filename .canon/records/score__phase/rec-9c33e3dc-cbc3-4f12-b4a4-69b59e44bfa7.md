---
{
  "id": "rec-9c33e3dc-cbc3-4f12-b4a4-69b59e44bfa7",
  "lifecycle_state": "done",
  "payload": {
    "effort": "evidence-layer",
    "ordinal": 4,
    "title": "aff verdict runs tests through a runner adapter"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-18T00:17:42+00:00",
  "relationships": {},
  "revision": "sha256:c94e3438b1774d851281ef03b13f2b19eca04b9598dad1600f8cf7f431b1e255",
  "subject": "runner-adapter"
}
---

## Problem

`aff verdict` is pytest-only. `_pytest_at` runs `python3 -m pytest`, `_FAILED_RE` scrapes `FAILED <nodeid>`, and `oracle_red.py` regexes `AssertionError` against `ImportError`. Every later audit step reruns tests the same way, so it would inherit those assumptions. A flaky witness also makes "fails at base" meaningless.

## Approach

Verdict calls `run_tests(worktree, test_ids, runner)` and reads JUnit XML (`runner-template`, `assertion-signal`). The manifest `runner` is an argv list with `{tests}` and `{report}`. An absent `runner` is `python3 -m pytest -o junit_family=xunit1 {tests} --junitxml={report}`. `<failure>` is `assertion_failed`, `<error>` is `errored`, and a skipped or missing case is `not_run`. A claim whose first run would pass is confirmed once in the same worktree; a witness that disagrees is `unstable` (`unstable-rerun`). The template is not hashed in this phase (`runner-template-freeze`). `oracle_red.py` stays for orchestra's close path.

## Exit criteria

1. `aff verdict` judges a claim through `run_tests` with no pytest stdout regex. Existing pass, hash-mismatch, and collection-error cases keep their results.
2. A fixture command that emits JUnit XML is judged with no change under `affidavit/`.
3. A witness that is `assertion_failed` on the first base run and `passed` on the confirmation run yields claim result `unstable` and a non-zero exit.
4. An absent `runner` uses the shipped pytest template. A `runner` that is not an argv list with `{tests}` and `{report}` fails manifest load.

## Landing

Branch `phase/runner-adapter`. Worktree `/home/andrewyin/affidavit--runner-adapter`. Base `main`. Close: commit the code on the phase branch, merge that branch into `main`, then commit the store on the primary checkout.

## Run

One sitting. No human stops. Every task is `subagent`.

Wave 1 is `parse-manifest-runner` (8 minutes) and `junit-run-tests` (18), so 18 minutes. Wave 2 is `verdict-through-runner` (22). Wave 3 is `verify-runner-adapter` (8). Phase elapsed is 48 minutes.

Wave 1 writes disjoint files: `parse-manifest-runner` edits `affidavit/manifest.py` and `tests/test_manifest.py`; `junit-run-tests` edits `affidavit/runner.py` and `tests/test_runner.py`. Wave 2 edits `affidavit/verdict.py` and `tests/test_verdict.py` and does not edit the wave 1 modules. Wave 3 runs the acceptance commands and does not add features.
