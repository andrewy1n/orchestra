---
{
  "id": "rec-070c4cbf-7d96-4b6f-ac1c-2d7aae7fc49d",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "cursor",
    "decisions": [
      "explicit-wheel"
    ],
    "effort": "package-layout",
    "estimate_minutes": 12,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "wheel-contents",
    "requirements": [
      "R15"
    ],
    "size": "M",
    "title": "Move effort_rollup into orchestra.score"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-28T07:47:55+00:00",
  "relationships": {},
  "revision": "sha256:f7a23911b3d1edfb0377df708ed9b54971811bbd1f8211c00f70b744c948ed8c",
  "subject": "score-effort-rollup"
}
---

## Description

R15: Importing `effort_rollup` from `orchestra.score` succeeds without inserting `scripts/` on `sys.path`.

## Approach

Move `scripts/effort_rollup.py` to `orchestra/score/effort_rollup.py`. The public function stays `effort_rollup`.

Update callers that load it as a loose script, including `tests/test_effort_rollup.py`, so they import `from orchestra.score.effort_rollup import effort_rollup` (or `from orchestra.score import effort_rollup` if the package re-exports it). Do not insert `scripts/` or the repo root on `sys.path` to make that import work.

Leave `scripts/build_skills.py`, `scripts/check_orchestra_plugin_names.py`, and `scripts/test.sh` in `scripts/`. Do not edit `tests/test_wheel_contents.py`, `orchestra/composer/`, or any `idea-triage` worktree.
