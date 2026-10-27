---
{
  "id": "rec-fa4ca44a-89ba-4723-aece-74583df85c0e",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "phase": "evidence-interface",
    "result": "pass",
    "revision": "a655bf41071f6783be3049a8107ac8e28c54ee55"
  },
  "provenance": {
    "sources": [
      "evidence-interface"
    ]
  },
  "record_type": "conductor:integration-report",
  "recorded_at": "2026-10-18T09:16:17+00:00",
  "relationships": {},
  "revision": "sha256:1d31629d97f470be70c6e64c964b552032f3ca17704749c74d9a1a9bed71a645",
  "subject": "evidence-interface",
  "time": {
    "observed": "2026-10-18T09:16:17+00:00",
    "recorded": "2026-10-18T09:16:17+00:00"
  }
}
---

## Interfaces

Contract adds `project:evidence-observation` (technique, base_rev, head_rev, result, claim_ids; optional effort/replay). `aff verdict` still judges then optionally records via `maybe_record_verdict_observation` → `adaptive-artifacts create --root <cwd>`. New `aff trail [--cwd|--claim|--technique]` lists via `adaptive-artifacts list` and prints JSON. Helper is `affidavit/observation.py` (subprocess only).

## Assumptions

Reviewed only brief specs/acceptances/invariants/design plus `main..a655bf4` tree (cli, observation, contract, tests); ignored execution-report/check-run/assessment/assignment material. Assumed disposable `store` fixture yields usable `.artifacts/resolved-contract.json` and that `adaptive-artifacts list --format json` returns `{records:[...]}` with nested `payload` as tests expect.

## Invariants

Judge path unchanged (`verdict.py` not in diff); record is post-stdout, best-effort, never flips exit. No `adaptive_artifacts` import; CLI name/type assembled to satisfy `test_no_store_tokens`. Store writes only through public CLI. No-store path leaves stdout/exit as before. Manifest/claims untouched.

## Conflicts

none
