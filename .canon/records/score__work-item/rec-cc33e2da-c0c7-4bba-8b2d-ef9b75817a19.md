---
{
  "id": "rec-cc33e2da-c0c7-4bba-8b2d-ef9b75817a19",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "verify-effort-brief-agent",
    "decisions": [
      "brief-storage",
      "brief-enforcement"
    ],
    "depends_on": [
      "brief-schema",
      "brief-skills"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "effort-brief",
    "requirements": [
      "R6",
      "R8"
    ],
    "size": "S",
    "title": "Verify the effort brief type and skills"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T17:23:33+00:00",
  "relationships": {},
  "revision": "sha256:74b5f5e3e2991448bc2b960106985266159588fa82f9477fbfcff7e8a7c6bbfc",
  "subject": "verify-effort-brief"
}
---

## Description

Prove the phase exit criteria hold together: run both test files, run the sync-then-validate integration check through the real `canon` CLI, then check this phase's own records with `orchestra analyze`.

R6: After `canon schemas sync` on a store whose `score` snapshot is `1.0.0`, the store snapshot of `score` has version `1.1.0`.

R8: After that sync, `canon validate` reports no error for a `score:effort` record created before the sync.

## Approach

Run the two test files, the integration test that runs `canon schemas sync` and `canon validate` as subprocesses on a temporary store pinned to `score` 1.0.0, and `orchestra analyze effort-brief` against the live store in plan stage. Report evidence only; do not edit the tree.
