---
{
  "id": "rec-be8e5f05-161e-4c83-b3e3-6a05ead51aff",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Start discuss inside the Textual process",
    "choice": "Promote and dismiss via CLI supersede; promote copies an agent prompt",
    "effort": "workflow-loop",
    "phase": "backlog-capture"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-10T09:21:34+00:00",
  "relationships": {},
  "revision": "sha256:6b93feddf366d78fc4e34cb7e9e3420ebd2b592e350986367163fe01f5e92691",
  "subject": "backlog-dashboard-actions",
  "time": {
    "as_of": "2026-10-10T09:21:34+00:00"
  }
}
---

## Rationale

The dashboard already clears human items by calling the adaptive-artifacts CLI and copies an agent prompt for the next step. Promote should supersede the backlog-item to `promoted` and copy a prompt that starts discuss (or incidental) for that effort; dismiss supersedes to `dismissed`. Starting discuss inside the Textual process would duplicate the skill loop and break the single-writer parent-session model.

## Counter-argument

In-process discuss from the dashboard would skip the copy-paste step. The cost is embedding skill orchestration in the UI, conflicting with “parent session writes records,” and a much larger surface than the existing Needs you prompt pattern.
