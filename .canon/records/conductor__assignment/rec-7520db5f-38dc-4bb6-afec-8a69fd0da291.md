---
{
  "id": "rec-7520db5f-38dc-4bb6-afec-8a69fd0da291",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard",
    "executor": "agent-verify-areas-and-ideas",
    "work_item": "verify-areas-and-ideas"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-29T22:35:56+00:00",
  "relationships": {},
  "revision": "sha256:624faf86034b1f2076831080a00417c0f7e0a069a7116e48b4db5c2ec13ee9a6",
  "subject": "verify-areas-and-ideas"
}
---

## Orientation

Parallel tasks in this wave edit disjoint files. Stay inside your task scope. Install node_modules in your worktree with `npm ci` in `dashboard/web/ui` when you need npm. Do not push.

Write root: `/home/andrewyin/orchestra/.worktrees/areas-and-ideas`

### Work-item (quote)

## Description

Prove the phase exit criteria hold together: run the integration test through `dashboard/bin/web` against this worktree's store, then every other phase check.

## Approach

Run each acceptance with `orchestra check` in the phase worktree. Do not edit the tree. Run the integration test first.

### Requirements (quote by id)

R1: `GET /api/areas` returns every active `composer:area` with its subject, title, and scope text.
R2: Each area in the response lists the ideas whose `payload.area` equals the area subject.
R3: The idea list includes ideas with status `open` or `promoted` and excludes `dismissed` and superseded ideas.
R4: An idea with both an effort and an area appears in the area's list and in the effort's backlog.
R5: Each idea in the response carries its area and its effort.
R6: The Home screen has an Areas section that lists each area with its open idea count.
R7: An area detail screen shows the scope text and the idea list, open ideas first.
R8: Promoted ideas show collapsed on the area screen and link to their effort or phase.
R9: The area screen has no promote or dismiss action.
R10: An area screen has a deep link that reloads to the same screen.
R11: A store with no `composer:area` records returns an empty list from the endpoint.

### Design / decisions (quote)

- The effort backlog output is the same as before.
- The area loader reads only through `store.py`.

- The snapshot types list in the loader can add `composer:area` without breaking foreign stores. The soft-type handling covers a store without that type.

- `idea-both-fields`: Show an idea in both the area view and the effort backlog

- `area-idea-states`: Show open and promoted ideas, with promoted collapsed

- `area-view-read-only`: The area view is read-only first

### Frozen oracle (do not edit)

Files in acceptance oracle_hashes are frozen. Do not edit them:
- ['tests/dashboard/test_areas.py']
An oracle hash or test-id change is a signed amendment in `.tuner/manifest.json`. orchestra verify verdict accepts or rejects it. A non-zero exit means the acceptance is not done.
