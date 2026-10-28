---
{
  "id": "rec-7ded4e4a-cdbb-44ff-a52b-cc0dbdf67594",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "composer",
    "executor": "cursor",
    "work_item": "engage-idea-input"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-28T07:39:56+00:00",
  "relationships": {},
  "revision": "sha256:d2b154953d4fd4ab86605e940c8abb57bd35bfa4bc1da7b78380642f68082eec",
  "subject": "engage-idea-input"
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/engage-from-idea--engage-idea-input` (branch task/engage-from-idea/engage-idea-input). Cursor worker.

### Work-item (quote)

## Description

R1: `engage` accepts the subject of an open `composer:idea` as the ask.
R2: `engage` lists open ideas from `orchestra view roadmap` when the user asks to start from an idea and names none.
R3: `engage` reads the named idea with `canon list --type composer:idea --subject <subject> --exact-subject`.
R4: `engage` refuses an idea whose status is not `open`.
R5: `engage` takes the idea's effort as the focus when the idea has an effort.
R6: `engage` routes an idea without an effort to `init` for a new effort.
R7: The routing line carries `idea: <subject> | none`.
R10: An idea stays `open` when the user stops before an effort or phase exists.
R11: The `engage` description names a triaged idea as an input.

## Approach

Edit `skills/engage/SKILL.md` and `tests/test_assess_routing.py`. (a) Frontmatter description: add that the ask may name a triaged idea. (b) Add an idea-input step after step 3: when the ask names the subject of an open `composer:idea`, or asks to start from an idea, accept it; when no subject is named, run `orchestra view roadmap` and list the open ideas grouped by area. Read the idea with a fenced `canon list --type composer:idea --subject <idea-subject> --exact-subject --state active --full`. Refuse an idea whose status is not `open` (say so and stop). Focus is the idea's `effort` when it has one; the ask then becomes a new phase of that effort (settle-phase with `phase: new`). An idea with no effort routes to `init` for a new effort; propose a focus slug from the idea subject and let the user confirm. State that engage writes nothing for the idea path and the idea stays `open` until `init` or `settle-phase` promotes it, so an idea stays open when the user stops first. (c) Replace the old Promote bullet in the parked-items step: promotion now happens through this path; keep Park and Dismiss as they are. (d) Add `idea: <subject> | none` to the routing line block. (e) Add a Do-not bullet: write the idea from engage. Tests: assert each of these in the skill text and that the new fenced `canon list` invocation is accepted by `skill_extraction.extract_invocations` with type `composer:idea`.
