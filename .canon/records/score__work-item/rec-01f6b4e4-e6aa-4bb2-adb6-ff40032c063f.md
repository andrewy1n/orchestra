---
{
  "id": "rec-01f6b4e4-e6aa-4bb2-adb6-ff40032c063f",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "verify-runner",
    "decisions": [
      "runner-template",
      "assertion-signal",
      "unstable-rerun",
      "runner-template-freeze"
    ],
    "depends_on": [
      "parse-manifest-runner",
      "junit-run-tests",
      "verdict-through-runner"
    ],
    "effort": "evidence-layer",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "runner-adapter",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5"
    ],
    "size": "S",
    "title": "Verify verdict runs through the runner adapter"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-18T00:15:18+00:00",
  "relationships": {},
  "revision": "sha256:0538f2d744fafd773d68f623ceec5c44ddd5a7dee9a6a3654df17a2b89d72724",
  "subject": "verify-runner-adapter"
}
---

## Description

Prove the phase exit criteria hold together: run `bin/aff verdict` through the existing cases and the fixture runner, then the unstable confirmation and the manifest template checks.

## Approach

Work in `/home/andrewyin/affidavit--runner-adapter` on branch `phase/runner-adapter`. Run the acceptance commands. Do not add features. A failure goes back to the task that owns that criterion.

1. `python3 -m pytest tests/test_verdict.py -q -k "pass_when or hash_mismatch or not_assertion or ignores_pytest_stdout"`
2. `python3 -m pytest tests/test_verdict.py -q -k fixture_junit`
3. `python3 -m pytest tests/test_verdict.py -q -k "unstable_when_confirmation or skips_confirmation"`
4. `python3 -m pytest tests/test_manifest.py -q -k "runner_absent or runner_invalid"`
