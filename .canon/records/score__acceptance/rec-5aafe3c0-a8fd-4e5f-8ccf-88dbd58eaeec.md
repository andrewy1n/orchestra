---
{
  "id": "rec-5aafe3c0-a8fd-4e5f-8ccf-88dbd58eaeec",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "check",
    "phase": "mypy-gate",
    "requirement": "R8",
    "verify_command": "f=orchestra/_type_probe.py; printf 'x: int = \"a\"\\n' > $f; uv run basedpyright >/dev/null 2>&1; rc=$?; rm -f $f; test $rc -ne 0"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T07:44:23+00:00",
  "relationships": {},
  "revision": "sha256:7cb10d59054ff07be082bc83739544cd68b8d7c718fe384b6bd2db22f1a4235d",
  "subject": "write-types-baseline-new-error"
}
---

