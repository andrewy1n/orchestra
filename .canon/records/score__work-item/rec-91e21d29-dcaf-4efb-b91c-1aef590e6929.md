---
{
  "id": "rec-91e21d29-dcaf-4efb-b91c-1aef590e6929",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "cursor",
    "decisions": [
      "explicit-wheel"
    ],
    "effort": "package-layout",
    "estimate_minutes": 6,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "wheel-contents",
    "requirements": [
      "R9",
      "R10",
      "R11"
    ],
    "size": "S",
    "title": "Let missing canon, suite, and check imports raise"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-28T07:47:54+00:00",
  "relationships": {},
  "revision": "sha256:4a01e49b813bb51cf1f456599a3138f66eb81a71aca05ca58570a7400f5ebb17",
  "subject": "propagate-import-errors"
}
---

## Description

R9: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.canon` cannot be imported.
R10: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.conductor.suite` cannot be imported.
R11: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.conductor.check` cannot be imported.

## Approach

In `orchestra/cli.py`, delete the three `try`/`except ModuleNotFoundError` blocks that bind canon (`open_store`, `StoreError`, `StoreBindingError`), `suite`, and check (`DEFAULT_TIMEOUT_S`, `git_head`, `run_check`) to `None`. Import those names at module level so a missing module raises `ModuleNotFoundError`.

Leave the `sessions` command's `ModuleNotFoundError` handler for `sessions-package`. Do not edit other subcommands. Do not edit `tests/test_wheel_contents.py` or `tests/test_cli_packaging.py`.

`phase/idea-triage` also edits `orchestra/cli.py`. Keep this diff inside the import block at the top of the file.
