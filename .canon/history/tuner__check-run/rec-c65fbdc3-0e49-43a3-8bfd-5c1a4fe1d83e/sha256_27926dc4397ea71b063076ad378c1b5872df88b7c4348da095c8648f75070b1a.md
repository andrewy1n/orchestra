---
{
  "id": "rec-c65fbdc3-0e49-43a3-8bfd-5c1a4fe1d83e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-0b870334-6288-4582-9ef8-bd802181b64b",
    "duration_s": 7.94676,
    "effort": "ci",
    "exit_code": 0,
    "informed_by": [
      "rec-0b870334-6288-4582-9ef8-bd802181b64b",
      "rec-0271249c-cf3f-410c-a735-384b6dbdd6d5"
    ],
    "method": "check",
    "output_sha256": "7fdfb1b52a17b6885a5d8ee67db90f57480e028c8116da2cc8518081c71732aa",
    "requirement": "R20",
    "result": "pass",
    "revision": "30de2366246662831be14e046fdb4dff9c660816",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T09:35:34+00:00",
  "relationships": {},
  "revision": "sha256:27926dc4397ea71b063076ad378c1b5872df88b7c4348da095c8648f75070b1a",
  "subject": "verify-wheel-smoke-clean"
}
---

orchestra --help: pass
canon --help: pass
canon init: pass
canon validate: pass
orchestra install --list: pass
import dashboard: pass
import dashboard.web: pass
import installer: pass
import installer.adapters: pass
