---
{
  "id": "rec-202b31bb-dba8-4bb0-ab9b-cae95af2386e",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "A plugin install made with sync-plugin.sh contains an executable se-workflow.tmux.",
    "effort": "dashboard",
    "method": "check",
    "phase": "tmux-plugin-entry",
    "verify_command": "d=$(mktemp -d) && bash scripts/sync-plugin.sh \"$d/p\" && test -x \"$d/p/se-workflow.tmux\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-02T19:35:21+00:00",
  "relationships": {},
  "revision": "sha256:2204114af1b61c2c553a322357b4ed539078a69ca7b4d96828f6ab3aa865ec91",
  "subject": "tmux-conf-removal-install",
  "time": {
    "as_of": "2026-10-02T19:35:21+00:00"
  }
}
---

