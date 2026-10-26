---
{
  "id": "rec-4e8c94cc-535b-4ee3-ac9e-e5c08eaa265f",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Two milestones web-home then web-depth; One fat phase web-ui-calm",
    "choice": "Five thin phases under milestone web-calm: milestone-nav, side-rail-calm, deep-links, phase-overview, task-graph",
    "effort": "dashboard",
    "phase": "milestone-nav"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-20T03:04:05+00:00",
  "relationships": {},
  "revision": "sha256:61d12982d037cd9083ebbd581b1596d00ee8c718ae794f12cdda440de6f9210a",
  "subject": "web-calm-phase-split",
  "time": {
    "as_of": "2026-10-20T03:04:05+00:00"
  }
}
---

## Rationale

Thin sequential phases under one milestone match the earlier dashboard UX split and put the highest-pain home-screen fixes (milestone grouping, journal off the rail) first. Each phase has a demable exit; the task graph waits until the home is calm.

## Counter-argument

Two milestones (home vs depth) would let "calm home" read as finished sooner on the dashboard. That was rejected because linking and phase overview are small enough to keep in the same milestone without blocking the first demos, and one milestone keeps the cutover story simpler.
