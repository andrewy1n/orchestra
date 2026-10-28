---
{
  "id": "rec-eb9da93b-ad27-45ae-a874-aa183ade45b5",
  "lifecycle_state": "active",
  "payload": {
    "effort": "composer",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_idea_command.py:sha256:2746435539449afe91d101c6a81d4f40129f4ac7821db9f24278aea86674cb51"
    ],
    "phase": "idea-triage",
    "requirement": "R7",
    "test_ids": [
      "tests/test_idea_command.py::test_r7_idea_command_refuses_duplicate_subject"
    ],
    "verify_command": "python3 -m pytest -q -p no:cacheprovider tests/test_idea_command.py::test_r7_idea_command_refuses_duplicate_subject"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-28T06:59:55+00:00",
  "relationships": {},
  "revision": "sha256:05b394261cfe349cc9c3e95a4a56f1f039286e622130910022b31820b7981c6a",
  "subject": "idea-capture-duplicate"
}
---

