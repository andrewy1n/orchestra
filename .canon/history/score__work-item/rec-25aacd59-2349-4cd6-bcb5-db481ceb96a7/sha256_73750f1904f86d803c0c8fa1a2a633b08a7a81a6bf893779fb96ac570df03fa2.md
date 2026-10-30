---
{
  "id": "rec-25aacd59-2349-4cd6-bcb5-db481ceb96a7",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "decisions": [
      "web-ci-job-shape",
      "ts-lint-tool",
      "lint-findings-policy"
    ],
    "depends_on": [
      "biome-lint",
      "web-ci-job",
      "agents-ts-section",
      "fix-type-errors"
    ],
    "effort": "dashboard",
    "estimate_minutes": 12,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "node-ci",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6",
      "R7",
      "R8",
      "R9",
      "R10"
    ],
    "size": "M",
    "title": "Verify Node CI and lint standard"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T18:51:52+00:00",
  "relationships": {},
  "revision": "sha256:73750f1904f86d803c0c8fa1a2a633b08a7a81a6bf893779fb96ac570df03fa2",
  "subject": "verify-node-ci"
}
---

## Description

Prove the phase exit criteria hold together: run the `ci.yml` web job commands locally through the real entry point, then every other phase check. R7 needs a human push; leave it unsigned and report it.

## Approach

Run each acceptance with `orchestra check`. Run the integration test first. Do not push. For R7, record the manual check-run as unsigned and name the three branches a human must push: the phase branch, a branch with a deliberate type error, and a branch with a deliberate lint finding.
