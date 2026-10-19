---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-060a643c-a5a1-4add-aa9c-eaaad4106e73",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "update-affidavit-resolve-only,break-legacy-paths",
    "choice": "keep-bin-and-tools-shims",
    "effort": "packaging",
    "phase": "pyproject-pypi"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-15T20:55:16+00:00",
  "relationships": {},
  "revision": "sha256:f18d13036ce6b8ae13bc9b6b43739b54152b86216f7831c711b4f2f7d76ce789",
  "stewardship": {
    "steward": "agent"
  },
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
