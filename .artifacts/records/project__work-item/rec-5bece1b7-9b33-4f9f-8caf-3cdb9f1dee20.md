---
{
  "base_kind": "task",
  "id": "rec-5bece1b7-9b33-4f9f-8caf-3cdb9f1dee20",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "install-docs-agent",
    "decisions": "",
    "effort": "packaging",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "cross-harness-install",
    "requirements": "R15",
    "size": "S",
    "title": "Document the host matrix and install commands"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-18T23:27:54+00:00",
  "relationships": {
    "depends_on": [
      "rec-7d73bd37-c7a9-464d-a75d-eb8fb9b94b47"
    ]
  },
  "revision": "sha256:f6894f530925348d9fba7870287cae03319ca2457b762336fa62c029bdd61c2b",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "install-docs"
}
---

## Description

R15: README documents the host matrix and the install commands.

## Approach

Add a README section with a host matrix table that matches the installer's provider matrix, the CLI install (`uv tool install`), per-host install commands, `--dry-run` first, `--global`/`--copy`/`--uninstall`, and the `npx skills add` tail. Add `tests/test_readme_matrix.py` that asserts every provider row and documented command appears and matches the matrix.
