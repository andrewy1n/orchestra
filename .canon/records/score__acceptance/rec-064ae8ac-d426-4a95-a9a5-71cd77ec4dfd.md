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
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-15T20:58:02+00:00",
  "relationships": {},
  "revision": "sha256:58bd94b3b581693cc5cdc03ecdada4f8a32cccdef2e58d61140f04f51c37984d",
  "subject": "verify-pyproject-pypi-shims",
  "time": {
    "as_of": "2026-10-15T20:58:02+00:00"
  }
}
---

