---
{
  "id": "rec-fd7dfe9f-f56d-4da8-aca1-244459d66d4b",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "sub-commit-stat-width",
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "dashboard-actions",
    "title": "Fit the commit stat to the pane width"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T03:16:21+00:00",
  "relationships": {},
  "revision": "sha256:65204c65cc5588fb5c8ea8cbc7cb8fca810c28e89ad68fb207e23444072a9c60",
  "subject": "commit-stat-width"
}
---

## Description

The commit screen runs `git show --stat` with git's default graph width, so at 80 columns a stat line wraps and splits its count from its graph. Size the stat to the screen width (`--stat=<width>`) and re-load on resize.
