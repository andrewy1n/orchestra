---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-a938be4f-fda4-4199-aa80-afbf9bc012a2",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "agent-affidavit,keep-se-workflow",
    "choice": "affidavit-cli-aff",
    "effort": "packaging",
    "phase": "rename-agent-affidavit"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-15T08:00:06+00:00",
  "relationships": {},
  "revision": "sha256:ca8eefdeebdea3126704132a9e19a5322dbfd5e05f0048edda884b800830c7d1",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "rename-product-name",
  "time": {
    "as_of": "2026-10-15T08:00:06+00:00"
  }
}
---

## Rationale

The shipped product name is `affidavit` (not `agent-affidavit` or `se-workflow`). Short CLI bin `aff` matches that brand and stays easy to type. One name across plugin id, package, contract project field, docs, and GitHub repo avoids dual branding while still unreleased.

## Counter-argument

Keeping `agent-affidavit` as the long form would match the old backlog wording and make the name more distinctive in marketplaces. It adds length without clear benefit once the short name is fixed as `affidavit`.
