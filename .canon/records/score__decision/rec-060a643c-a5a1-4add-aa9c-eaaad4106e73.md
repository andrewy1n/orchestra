---
{
  "id": "rec-060a643c-a5a1-4add-aa9c-eaaad4106e73",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "update-affidavit-resolve-only,break-legacy-paths",
    "choice": "keep-bin-and-tools-shims",
    "effort": "packaging",
    "phase": "pyproject-pypi"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-15T20:55:16+00:00",
  "relationships": {},
  "revision": "sha256:627598f9a378ad07dd8acb7c66b206831fa3e414bf222580280b791b551b7b87",
  "subject": "aa-checkout-shims",
  "time": {
    "as_of": "2026-10-15T20:55:16+00:00"
  }
}
---

## Rationale

Affidavit resolve and tests locate the CLI via `ADAPTIVE_ARTIFACTS_ROOT/.../tools/artifacts.py` and plugin `bin/adaptive-artifacts`. Approach 1 leaves the affidavit tree alone. Keeping thin shims at those paths (delegating into the new package/entry point) preserves plugin installs and the affidavit test suite without a coupled affidavit change in this phase.

## Counter-argument

Updating affidavit's resolve order and test harness to use only `python -m` / installed scripts would delete legacy paths and match a pure packaging world. That couples AA Landing to affidavit edits and expands scope beyond the chosen AA-first cut.
