---
{
  "id": "rec-2edb2fb6-b62f-487e-8c5e-9e24ba019ef8",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "store-client-agent",
    "decisions": [
      "affidavit-store-client",
      "dependency-direction",
      "call-style",
      "three-repos"
    ],
    "effort": "library-boundary",
    "estimate_minutes": 15,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "affidavit-library",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6"
    ],
    "size": "M",
    "title": "Call Project from observation and binding"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-21T10:23:08+00:00",
  "relationships": {},
  "revision": "sha256:6ea03c4234c5a81a1d75e135a4de2c7eb89919f4941b61029f9f5b89a681d704",
  "subject": "store-client"
}
---

## Description

R1: `affidavit.observation` creates an evidence-observation by calling `Project.create`.
R2: `affidavit.observation` lists evidence-observations by calling `Project.list`.
R3: `affidavit.binding` creates an evidence-binding by calling `Project.create`.
R4: `affidavit.binding` lists evidence-bindings by calling `Project.list`.
R5: No module under `affidavit/` starts a process to run `adaptive-artifacts`.
R6: The evidence-layout test passes when affidavit source imports `adaptive_artifacts` and names `project:` record types.

## Approach

In `affidavit.observation` and `affidavit.binding`, open the store with `open_store` and call `Project.create` and `Project.list`. Delete the subprocess clients. Delete the word-ban test that forbids `adaptive-artifacts` and `project:`. Keep a test that fails if a module under `affidavit/` starts `adaptive-artifacts`. Do not edit `affidavit/verdict.py`, `affidavit/oracle_red.py`, or `affidavit/cli.py`.
