---
{
  "id": "rec-ec078b21-77e1-4dbe-9ae4-8282cf8cbb62",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "phase filter without headers, phase column only",
    "choice": "Group the task table into collapsible phase sections, folding older done phases",
    "effort": "dashboard-ui",
    "phase": "task-navigation"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-09-30T23:09:14+00:00",
  "relationships": {},
  "revision": "sha256:eef74c6b4f2c6fd9c62f2c563a87e193c8e5fc303de1ada48e4ebc8672bfcdcf",
  "subject": "phase-sections",
  "time": {
    "as_of": "2026-09-30T23:09:14+00:00"
  }
}
---

## Rationale

Grouped sections make phases read as structure, not as a task attribute. Collapsing done and planned phases, and folding more than two done phases into one row, keeps a long effort to a few header lines.

## Counter-argument

With many phases, header rows still add lines and extra keypresses compared with a single phase filter.
