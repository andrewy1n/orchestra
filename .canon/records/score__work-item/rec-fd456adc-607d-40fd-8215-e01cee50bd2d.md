---
{
  "id": "rec-fd456adc-607d-40fd-8215-e01cee50bd2d",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "parent",
    "depends_on": [
      "package-move"
    ],
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "dashboard-package",
    "title": "Update the plugin install, tmux conf and README"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T19:07:30+00:00",
  "relationships": {},
  "revision": "sha256:1101ca428f9ca10f1f1e0946ed13b6b28f5d1efad720384bbad051fe2c96b7c6",
  "subject": "package-install"
}
---

## Description

Make sync-plugin.sh copy `dashboard/` into the install. Point `dashboard/tmux.conf` at the new launcher path. Update the README paths and the status-line example. The install copy must run `bin/dashboard --once`.
