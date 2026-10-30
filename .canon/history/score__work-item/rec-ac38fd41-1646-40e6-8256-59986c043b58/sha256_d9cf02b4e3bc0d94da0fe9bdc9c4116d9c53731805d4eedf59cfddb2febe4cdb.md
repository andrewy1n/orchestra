---
{
  "id": "rec-ac38fd41-1646-40e6-8256-59986c043b58",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "decisions": [
      "web-ci-job-shape"
    ],
    "effort": "dashboard",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "node-ci",
    "requirements": [
      "R1"
    ],
    "size": "S",
    "title": "Add the web CI job"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T18:47:41+00:00",
  "relationships": {},
  "revision": "sha256:d9cf02b4e3bc0d94da0fe9bdc9c4116d9c53731805d4eedf59cfddb2febe4cdb",
  "subject": "web-ci-job"
}
---

## Description

R1: `.github/workflows/ci.yml` has a `web` job that runs `npm ci`, `npm run lint`, `npm run check`, `npm test`, `npm run build` in order in `dashboard/web/ui`, with no path filter.

## Approach

Add the `web` job after `types` in `ci.yml`: `actions/checkout@v4`, `actions/setup-node@v4` with `node-version: 22`, `cache: npm`, `cache-dependency-path: dashboard/web/ui/package-lock.json`, then one `run` step per command with `working-directory: dashboard/web/ui`. Use `timeout-minutes: 15`. Do not change other jobs or the triggers. Keep `tests/test_ci_workflow.py` passing.
