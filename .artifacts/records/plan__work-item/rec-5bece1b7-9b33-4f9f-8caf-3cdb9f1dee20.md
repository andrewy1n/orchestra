---
{
  "id": "rec-5bece1b7-9b33-4f9f-8caf-3cdb9f1dee20",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "install-docs-agent",
    "decisions": [],
    "depends_on": [
      "native-adapters"
    ],
    "effort": "packaging",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "cross-harness-install",
    "requirements": [
      "R15"
    ],
    "size": "S",
    "title": "Document the host matrix and install commands"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-18T23:27:54+00:00",
  "relationships": {},
  "revision": "sha256:611d3b278e37d2d57143e035236c360f50e6756f5bb02ca049686f2a29aa12d5",
  "subject": "install-docs"
}
---

## Description

R15: README documents the host matrix and the install commands.

## Approach

Add a README section with a host matrix table that matches the installer's provider matrix, the CLI install (`uv tool install`), per-host install commands, `--dry-run` first, `--global`/`--copy`/`--uninstall`, and the `npx skills add` tail. Add `tests/test_readme_matrix.py` that asserts every provider row and documented command appears and matches the matrix.
