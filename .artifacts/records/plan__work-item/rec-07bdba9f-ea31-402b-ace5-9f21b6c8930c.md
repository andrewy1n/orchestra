---
{
  "id": "rec-07bdba9f-ea31-402b-ace5-9f21b6c8930c",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "trace-plan",
    "depends_on": [
      "contract-loop"
    ],
    "effort": "workflow-loop",
    "executor": "subagent",
    "kind": "deliver",
    "phase": "evidence-loop",
    "title": "Stamp tasks with requirements and decisions"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-05T02:19:52+00:00",
  "relationships": {},
  "revision": "sha256:f2cbb6c969b3d4871c6fccc9a5d8602082e0e21e3eaeacabe2085e2fe092e791",
  "subject": "trace-plan"
}
---

## Description

Stamp each planned task with the requirements and design decisions it implements.

## Approach

In `skills/plan-phase/SKILL.md`, when a `project:specification` exists for the phase, set work-item payload `requirements` to the comma-separated requirement ids that task implements and `decisions` to the comma-separated decision subjects it follows. Set each acceptance payload `requirement` to one of those ids. Several acceptances keep the existing subject-suffix rule. When no specification exists, omit the new fields.

Do not write `assessment` or `integration-report` from this skill. Dependencies stay `--rel depends_on`. Do not write `ready` or `wave`.

Add `tests/test_plan_trace.py`. It asserts the skill's work-item create payloads include `requirements` and `decisions`, and the acceptance payloads include `requirement`, and that those invocations are contract-legal via `skill_extraction.check_skill_text`.

Do not edit `discuss`, `execute-phase`, or `verify-work`.
