---
{
  "id": "rec-32cf33bf-d84e-4bef-bf7b-5071e35e21da",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "composer",
    "executor": "inline",
    "work_item": "composer-test-wiring"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-27T23:51:31+00:00",
  "relationships": {},
  "revision": "sha256:ace9d01709fac07b9ccae4abcf664f7db1dfc359f35f6ad810b3ea8138cefda0",
  "subject": "composer-test-wiring"
}
---

## Orientation

Wave 2, with composer-live-store. Inline executor. The two tasks touch disjoint files; composer-live-store changes only the store.

Write root: `/home/andrewyin/orchestra/.worktrees/composer-schema--composer-test-wiring`

### Work-item (quote)

R13: `tests/test_boundaries.py` reports a module under `orchestra/composer/` that imports `orchestra.conductor`.
R14: `tests/test_boundaries.py` accepts a module under `orchestra/composer/` that imports `orchestra.canon` or `orchestra.score`.

Approach: In `tests/test_boundaries.py` add `composer` to `COMPONENTS`, add `"composer": {"canon", "score", "composer"}` to `ALLOWED`, and add `composer` to the `stage` set. Add `orchestra/composer/schemas/composer.json` to `SCHEMA_FILES` in `tests/conftest.py` and `tests/tuner/conftest.py`, and to `SCHEMA_PATH` in `tests/canon_support.py`. Leave the `score,conductor,tuner` store lists unchanged. Do not edit files that have uncommitted work in the primary checkout.

### Design / decisions (quote)

Invariants:
- `score.json`, `conductor.json` and `tuner.json` are unchanged.
- composer imports only canon and score.

composer-score-direction: composer sits above score: composer:idea has an optional effort ref to score:effort; score is unchanged

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen: `tests/test_composer_schema.py`.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.tuner/manifest.json`. orchestra verify verdict accepts or rejects it. A non-zero exit means the acceptance is not done.
