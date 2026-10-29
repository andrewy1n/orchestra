---
{
  "id": "rec-c9eb94bf-00d4-4fef-b5a6-60b4a400e75e",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "status-cli",
    "result": "pass",
    "revision": "eecc8ea95183ea08c7b7ac9d452e7636503ce050",
    "verdict": "pass",
    "work_item": "status-cli"
  },
  "record_type": "conductor:execution-report",
  "recorded_at": "2026-10-29T20:21:17+00:00",
  "relationships": {},
  "revision": "sha256:ec0a79fd06be22112f626c5c2eea4bbec0bb989c2ace562ab598a2932ad44221",
  "subject": "status-cli"
}
---

subject: status-cli
kind: deliver
result: pass
revision: eecc8ea95183ea08c7b7ac9d452e7636503ce050
evidence: Added orchestra/status_cli.py (add_parser, run; imports dashboard.backend lazily) and registered the status subcommand in orchestra/cli.py; README CLI table gained a status row. orchestra status [DIR] loads the snapshot, merges landings with landings_for_snapshot, and prints "<effort>: running <n>, ready <n>, needs-you <n>" per effort; --count prints the merged needs-you total as a bare integer. Checks: pytest tests/test_orchestra_status.py 2 passed; boundaries, cli surface, cli packaging, web dashboard, web launch, remove_textual: 50 passed; basedpyright 0 errors; ruff clean on orchestra/status_cli.py and orchestra/cli.py.
observations: ruff reports F401 (unused json) at tests/test_orchestra_status.py:5, a frozen oracle file.
needs_human: false
