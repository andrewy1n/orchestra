---
{
  "base_kind": "event",
  "id": "rec-ebcffda4-ba5f-4804-84eb-bd3398394ff2",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e",
    "duration_s": 0.297568,
    "effort": "packaging",
    "exit_code": 0,
    "method": "check",
    "output_sha256": "db22166d9e2340ec15c31664062bdb5968941e358313099a118724876d5b877a",
    "requirement": "R3",
    "result": "pass",
    "revision": "db2b7e9f447a6d63b61be244296fa998f1395205",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "aa-uv-tool-install-proof-store"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-15T21:14:10+00:00",
  "relationships": {
    "informed_by": [
      "rec-d9c4add2-b3a0-4106-8778-46d3711d3c7e",
      "rec-49fcdf7d-a306-4085-b487-b827b0b7f4cd"
    ]
  },
  "revision": "sha256:d3c77529d2eae0f6a58067f2751c79508af4f1d0c1dab6173965de1c020abe3e",
  "subject": "aa-uv-tool-install-proof-store",
  "time": {
    "observed": "2026-10-15T21:14:10+00:00",
    "recorded": "2026-10-15T21:14:10+00:00"
  }
}
---

prove_uv_tool_install: ok url=git+file:///home/andrewyin/adaptive-artifacts@db2b7e9f447a6d63b61be244296fa998f1395205 bin=/tmp/aa-uv-tool-X5s3Ix/bin/adaptive-artifacts
Resolved 1 package in 1ms
Installed 1 package in 6ms
 + adaptive-artifacts==0.1.0 (from git+file:///home/andrewyin/adaptive-artifacts@db2b7e9f447a6d63b61be244296fa998f1395205)
Installed 2 executables: aa, adaptive-artifacts
