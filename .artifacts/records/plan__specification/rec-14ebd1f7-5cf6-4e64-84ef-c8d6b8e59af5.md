---
{
  "id": "rec-14ebd1f7-5cf6-4e64-84ef-c8d6b8e59af5",
  "lifecycle_state": "active",
  "payload": {
    "effort": "workflow-loop",
    "phase": "phase-proof-packet",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6",
      "R7"
    ],
    "weight": "full"
  },
  "record_type": "plan:specification",
  "recorded_at": "2026-10-19T03:53:13+00:00",
  "relationships": {
    "supersedes": [
      "rec-ddf71f72-4069-45d5-b9c9-e2031681ba0d"
    ]
  },
  "revision": "sha256:07184bd5d130f75f7d1bd56fe6cb8dc5cfdce82a6b697501320bb212d395b8e7",
  "subject": "phase-proof-packet",
  "time": {
    "as_of": "2026-10-19T03:53:13+00:00"
  }
}
---

## Requirements

R1: A project:proof-packet observation type exists in the orchestra contract with payload phase, effort, revision, base, and kind (demo|commands|claims|audit-triage|mixed), and required body sections Look, Machine, Attention, and Diff.
R2: The handoff view exposes a latest-proof role that selects proof-packet records so a finished phase's Look path appears without opening the full store.
R3: Structured settle/plan writes a ## Proof section on the phase body declaring kind and what looking means before work-items are materialized.
R4: execute-phase assembles and creates a proof-packet at the phase-head revision after the phase gate passes and before Landing merge or phase-done language, and refuses to call the phase complete without a packet at that revision.
R5: When the work repo has .affidavit/manifest.json, execute-phase pulls aff trail and aff audit pointers into Machine and Attention without inventing verdict prose.
R6: Incidental or no-Landing work still gets a proof-packet when code or claims changed; skip only when there was nothing to inspect.
R7: The dashboard phase detail loads the latest project:proof-packet for that phase and shows Look and Attention as a first-class Proof surface (tab or overview block), with a muted chip when a packet exists; it is not a blocking Needs-you item.

## Acceptance criteria

Each Rn is verified by a thin acceptance on the implementing or verification task: contract/schema checks for R1–R2; skill-text or fixture checks for R3–R6; dashboard model/screen tests for R7; verification task smoke creates or asserts a packet Look section at a SHA and confirms the dashboard detail path can load it.

## Constraints

No new aff verbs in this phase. Packet write is required; human signed_by on every phase is not required in v1. Do not overload project:integration-report for this purpose. Proof UI must not invent a second Needs-you gate.

## Non-goals

Auto-generated PR review essays. Walkthrough UX inside aff verdict. Replacing the phase-end reviewer or suite gates. Mandatory demo sign-off. A separate full-screen proof browser beyond phase detail.

## Invariants

Machine section holds pointers (record ids, claim ids, re-run commands), not paraphrased pass/fail essays. One packet subject per phase slug; supersede or replace when phase head moves after a fix pass. Dashboard Proof shows the same Look/Attention text as the record body.

## Assumptions

Existing aff audit, trail, and verdict CLIs are sufficient inputs when an affidavit manifest is present. Handoff role selection can surface the latest proof-packet per effort the same way other handoff roles work. Phase detail already hosts Spec/Design/Evidence tabs that Proof can sit beside.
