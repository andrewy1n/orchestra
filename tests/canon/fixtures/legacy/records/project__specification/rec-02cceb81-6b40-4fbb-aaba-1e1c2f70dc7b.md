---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-02cceb81-6b40-4fbb-aaba-1e1c2f70dc7b",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "workflow-loop",
    "phase": "claim-witnesses",
    "requirements": "R1,R2,R3,R4,R5,R6",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-16T09:24:54+00:00",
  "relationships": {},
  "revision": "sha256:61831a5bd248e758b3eac083c13c10ca6eb498d943649463c6acf6912ff1b63b",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "claim-witnesses",
  "time": {
    "as_of": "2026-10-16T09:24:54+00:00"
  }
}
---

## Requirements

R1: For tdd and check done closes, close-batch resolves each entry's check_run_id from the artifact store and refuses unless the stored check-run exists and matches the request on criterion_id, runner, result, and revision.

R2: For tdd done closes, close-batch resolves red_check_ru
