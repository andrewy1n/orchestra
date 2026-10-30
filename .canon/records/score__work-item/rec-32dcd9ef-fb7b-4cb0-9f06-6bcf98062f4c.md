---
{
  "id": "rec-32dcd9ef-fb7b-4cb0-9f06-6bcf98062f4c",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "subagent-engage-place-step",
    "decisions": [
      "placement-record-link"
    ],
    "effort": "dashboard",
    "estimate_minutes": 4,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "effort-area-link",
    "requirements": [
      "R8"
    ],
    "size": "XS",
    "title": "Name orchestra place in the engage skill"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-30T07:05:13+00:00",
  "relationships": {},
  "revision": "sha256:dfeea674f33a8add9912ee7bdc75aa4fd7bb5f409d823d404d7e195ae3b64940",
  "subject": "engage-place-step"
}
---

## Description

R8: The `engage` skill names `orchestra place` as the step that gives a new effort its area.

## Approach

Edit `skills/engage/SKILL.md`: after the step that creates or reuses an effort, add one step. For a new effort, ask which area it belongs to and run `orchestra place <effort> <area>`. Keep the wording short. If the skill text is copied into other skill folders by a sync script, run it.
