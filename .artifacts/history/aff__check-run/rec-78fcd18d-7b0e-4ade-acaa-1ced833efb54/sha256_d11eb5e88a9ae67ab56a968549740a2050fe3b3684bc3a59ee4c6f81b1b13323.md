---
{
  "id": "rec-78fcd18d-7b0e-4ade-acaa-1ced833efb54",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "pyproject-pypi-review",
    "effort": "packaging",
    "evidence_kind": "review",
    "method": "review",
    "result": "pass",
    "revision": "5257818a25994a1b41742f10c48d12cb7e5d767c",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "pyproject-pypi-review"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-15T21:19:18+00:00",
  "relationships": {},
  "revision": "sha256:d11eb5e88a9ae67ab56a968549740a2050fe3b3684bc3a59ee4c6f81b1b13323",
  "subject": "pyproject-pypi-review",
  "time": {
    "observed": "2026-10-15T21:19:18+00:00",
    "recorded": "2026-10-15T21:19:18+00:00"
  }
}
---

verdict: PASS
findings: []
integration:
  interfaces: Affidavit phase head documents git+ uv tool install and deferred PyPI; AA phase/pyproject-package adds pyproject.toml, src/adaptive_artifacts, shims, and prove_uv_tool_install.sh.
  assumptions: AA continuity-question answered and decision pyproject-package-layout satisfy R8; prove script git+file default is R2 equivalent; AA merge is that repo's Landing.
  invariants: Affidavit product code unchanged aside from README; CLI boundary and shim paths preserved; no PyPI or affidavit packaging metadata.
  conflicts: none
