---
{
  "id": "rec-ef1901ba-46da-4daf-a533-cb14f4552b2a",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "reviewer judgment finding",
    "claim": "skills still document affidavit.oracle_red Python API while close-batch is CLI-only",
    "effort": "workflow-loop",
    "invalidated_when": "docs updated or human clears",
    "needs": "human"
  },
  "provenance": {
    "sources": [
      "reviewer judgment finding"
    ]
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-21T07:05:34+00:00",
  "relationships": {},
  "revision": "sha256:a54d930bf2853907e55cc08661d84c1589e966ef2ac313822e7d6eb576115423",
  "subject": "review-skills-oracle-red-docs"
}
---

## Evidence

verify-work/SKILL.md and plan-phase oracle-author still mention is_assertion_level_red import.

## Consequence

Agents may still try Python import path for assertion-red.

## Follow-up

Human decide whether doc cleanup is this phase or follow-up backlog.
