---
{
  "id": "rec-e38f41fe-528c-4cd6-9ec7-2f8c405e2bdf",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "check",
    "phase": "mypy-gate",
    "requirement": "R8",
    "verify_command": "f=orchestra/_type_probe.py; printf 'x: int = \"a\"\\n' > $f; uv run basedpyright >/dev/null 2>&1; rc=$?; rm -f $f; test $rc -ne 0"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T07:44:33+00:00",
  "relationships": {},
  "revision": "sha256:56821df6b77a4fa29d7233c48913c44b2959fcebe11830c86c1bf32e678d6144",
  "subject": "verify-mypy-gate-new-error"
}
---

