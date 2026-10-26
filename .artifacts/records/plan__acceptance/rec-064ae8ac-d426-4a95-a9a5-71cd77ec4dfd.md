---
{
  "id": "rec-064ae8ac-d426-4a95-a9a5-71cd77ec4dfd",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Exit 2: plugin bin/adaptive-artifacts and tools/artifacts.py still run the CLI",
    "effort": "packaging",
    "method": "check",
    "phase": "pyproject-pypi",
    "requirement": "R4",
    "verify_command": "~/adaptive-artifacts/bin/adaptive-artifacts --help >/dev/null && python3 ~/adaptive-artifacts/tools/artifacts.py --help >/dev/null"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-15T20:58:02+00:00",
  "relationships": {},
  "revision": "sha256:c0702096ff0a4658b68062f434a4e1f9f0be7a298bd327319f5b8065291dd041",
  "subject": "verify-pyproject-pypi-shims",
  "time": {
    "as_of": "2026-10-15T20:58:02+00:00"
  }
}
---

