---
{
  "id": "rec-2be0ead2-7677-47d2-9ce4-9ba5ffcdd003",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Auto-detect stage from work-item state; separate command for close",
    "choice": "Explicit --stage plan|close flag, default plan",
    "effort": "workflow-loop",
    "phase": "spec-analyze"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-29T07:59:32+00:00",
  "relationships": {},
  "revision": "sha256:697dce64e277644d4cad631e1e0084ec2f31f0243dc390ab6e8e7e102b28aa38",
  "subject": "analyze-stage-flag"
}
---

## Rationale

Evidence checks make no sense before any task has run. An explicit `--stage plan|close` flag keeps the output a function of the arguments and the store. Each skill names the stage it runs, and tests pin both.

## Counter-argument

Auto-detecting the stage from work-item state removes the flag and removes the chance that an agent runs the wrong stage. The cost is that one command gives different results at different times, which is harder to test and explain. A wrong stage argument is a smaller risk than hidden state.
