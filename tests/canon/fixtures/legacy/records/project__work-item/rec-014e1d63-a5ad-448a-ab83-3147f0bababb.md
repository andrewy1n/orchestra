---
{
  "base_kind": "task",
  "id": "rec-014e1d63-a5ad-448a-ab83-3147f0bababb",
  "identity": "unknown",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "inline",
    "decisions": "aa-resolve-order",
    "effort": "packaging",
    "estimate_minutes": 30,
    "executor": "inline",
    "kind": "deliver",
    "phase": "plugin-root-and-cli",
    "requirements": "R2",
    "size": "M",
    "title": "Unify AA binary resolution"
  },
  "record_type": "project:work-item",
  "recorded_at": "2026-10-14T08:36:31+00:00",
  "relationships": {},
  "revision": "sha256:5aa1a90ab6bddd41803c8f01ba19f54253fe0f1f4704ab3aad86ca5ccd2b3b46",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "shared-aa-resolver"
}
---

## Description

One shared adaptive-artifacts binary resolver used by `se_workflow.aa` and `dashboard.artifact_store`, with order env override → plugin-root/sibling → PATH, and no quiet `~/adaptive-artifacts` primary fallback.

## Approach

1. Extract shared `resolve_aa_command()` (keep in `se_workf
