---
{
  "id": "rec-d16228da-0add-439f-bfe8-ced554846bc5",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "method": "check",
    "phase": "declared-install",
    "requirement": "R3",
    "verify_command": "python3 -c 'import pathlib; t=pathlib.Path(\"pyproject.toml\").read_text(); i=t.index(\"\\ndependencies\"); chunk=t[i:t.index(\"]\", i)]; assert \"affidavit\" not in chunk'"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-22T06:42:12+00:00",
  "relationships": {},
  "revision": "sha256:8c540315abafbd4beab98c85120cd65859ebe8755c8477946700edee294551b2",
  "subject": "package-metadata-optional",
  "time": {
    "as_of": "2026-10-22T06:41:39+00:00"
  }
}
---

