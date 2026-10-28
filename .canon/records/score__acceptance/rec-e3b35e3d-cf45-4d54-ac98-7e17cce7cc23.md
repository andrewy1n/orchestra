---
{
  "id": "rec-e3b35e3d-cf45-4d54-ac98-7e17cce7cc23",
  "lifecycle_state": "active",
  "payload": {
    "effort": "package-layout",
    "method": "check",
    "phase": "wheel-contents",
    "requirement": "R23",
    "verify_command": "python3 -c \"from pathlib import Path; t = Path('README.md').read_text(); assert '--no-project' not in t\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-28T07:16:09+00:00",
  "relationships": {},
  "revision": "sha256:8e1357e2d36cee64baa6615be4ffa9e64be0641925cfb444b6789e2dff40142b",
  "subject": "suite-commands-readme"
}
---

