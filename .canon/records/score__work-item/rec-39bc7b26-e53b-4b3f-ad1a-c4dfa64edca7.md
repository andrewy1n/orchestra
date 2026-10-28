---
{
  "id": "rec-39bc7b26-e53b-4b3f-ad1a-c4dfa64edca7",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "cursor",
    "decisions": [
      "backlog-conversion-method"
    ],
    "depends_on": [
      "idea-dashboard-switch",
      "idea-views-engage"
    ],
    "effort": "composer",
    "estimate_minutes": 12,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "backlog-to-idea",
    "requirements": [
      "R1",
      "R2",
      "R5",
      "R6",
      "R16"
    ],
    "size": "M",
    "title": "Remove the two score types and prove the conversion"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-28T06:23:01+00:00",
  "relationships": {},
  "revision": "sha256:2a4c48e14892c3c49a937762b7f401c5a36dba64494a2b55d5948329efa3aa31",
  "subject": "drop-backlog-types"
}
---

## Description

R1: Each live `score:backlog-item` becomes a `composer:idea` with the same id, subject, body and payload.
R2: Each history snapshot of a converted record has type `composer:idea`.
R5: The score module declares no `score:backlog-item` type.
R6: The score module declares no `score:feedback` type.
R16: No tracked file outside `docs/history/` names `score:backlog-item` or `score:feedback`.

## Approach

Remove `backlog-item` and `feedback` from `orchestra/score/schemas/score.json`; no version change. Replace `tests/test_backlog_item.py` with `tests/test_idea_conversion.py`: build a temporary git store whose snapshots hold a score module that still declares `backlog-item` plus the composer module, create backlog records and supersede one so history exists, call `orchestra.canon.migrate.apply_steps(Store(<.canon>), [{"rename_type": {"score:backlog-item": "composer:idea"}}])`, commit, and assert ids, subjects, bodies, payloads and history types. Add `tests/test_retired_types.py`: load the score module and assert neither type exists; scan `git ls-files` outside `docs/history/` and `.canon/` for the two retired names, building the names from parts so the test does not contain them.
