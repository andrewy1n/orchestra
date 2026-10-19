---
{
  "base_kind": "task",
  "id": "rec-b4e323ec-86bf-4114-8bfd-8e75636fbfcb",
  "identity": "unknown",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "decisions": "rename-product-name,rename-clean-break-scope",
    "effort": "packaging",
    "estimate_minutes": 20,
    "executor": "inline",
    "kind": "deliver",
    "phase": "rename-agent-affidavit",
    "requirements": "R2",
    "size": "L",
    "title": "Rename se_workflow package and CLI to affidavit / aff"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-15T08:01:49+00:00",
  "relationships": {},
  "revision": "sha256:005f6a3d510a0ba9d2ba3bf46ec76fab5631d0f9c02c3aaef8dad43ef6d2bdef",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "rename-package-cli"
}
---

## Description

Rename the Python package `se_workflow/` to `affidavit/`, replace `bin/se-workflow` with `bin/aff`, and update all in-repo imports/callers so the CLI entry is `aff`.

## Approach

1. Move/rename `se_workflow/` → `affidavit/` (keep module layout); update `__init__` / package docs strings.
2. Add `bin/aff` launcher importing `affidavit.cli`; delete `bin/se-workflow`.
3. Update `dashboard/`, scripts, and any other Python imports from `se_workflow` to `affidavit`.
4. Point CLI prog name / help text at `aff`.
5. Leave plugin manifests and contract project field for the next task if still needed for a green import graph; do not leave a permanent `se-workflow` bin alias.
