---
{
  "id": "rec-54efcdd0-8bb1-403b-b7b9-cc79ab97961b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "prefix + D, a custom key table",
    "choice": "prefix + A opens the dashboard popup; prefix + S opens a side pane",
    "effort": "dashboard",
    "phase": "tmux-integration"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-02T03:16:30+00:00",
  "relationships": {},
  "revision": "sha256:95e754e67bb67001a720c35e7decf842cc81b9d5c7763fdceb3549d5c0a8cdab",
  "subject": "tmux-dashboard-keys",
  "time": {
    "as_of": "2026-09-29T23:13:45+00:00"
  }
}
---

## Rationale

`prefix + d` and `prefix + D` are already bound (detach, choose-client) in the user's tmux config. `A` (artifacts) and `S` (side) are free and easy to remember. A popup is the on-demand view; a side pane is the always-on option.

## Counter-argument

Capital letters need Shift. A two-key table (for example prefix + a, then d) would free more keys for later dashboard actions.
