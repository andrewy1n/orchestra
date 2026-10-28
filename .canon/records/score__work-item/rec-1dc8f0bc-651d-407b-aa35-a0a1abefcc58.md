---
{
  "id": "rec-1dc8f0bc-651d-407b-aa35-a0a1abefcc58",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "cursor",
    "decisions": [],
    "effort": "composer",
    "estimate_minutes": 3,
    "executor": "inline",
    "kind": "deliver",
    "phase": "backlog-to-idea",
    "requirements": [
      "R8"
    ],
    "size": "XS",
    "title": "Add the idea-without-effort case to the handoff view test"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-28T06:30:25+00:00",
  "relationships": {},
  "revision": "sha256:ac7caa7c32988bfda8bbce4ff83c380de3ad50dd3f2502741645ef7b161e4846",
  "subject": "fix-idea-views-effort-case"
}
---

## Description

R8: `orchestra handoff` lists each open `composer:idea` that carries an effort under that effort.

## Approach

In tests/test_views.py extend the handoff backlog test with an open idea that has no effort and assert it is absent from the handoff.
