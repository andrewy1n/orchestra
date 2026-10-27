---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-bdbd3014-f9fa-4e3a-be6c-9c6984a101b8",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "phase": "web-write-body",
    "requirements": "R1,R2,R3",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-20T08:30:44+00:00",
  "relationships": {},
  "revision": "sha256:fbdffc93b9c061d825b53749b1bd0358c920fc25221291816a57efdbd8e85679",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "web-write-body",
  "time": {
    "as_of": "2026-10-20T08:30:44+00:00"
  }
}
---

## Requirements

R1: FastAPI POST /api/backlog with a JSON body and no query string dismisses an open backlog item.
R2: FastAPI POST /api/needs with a JSON body and no query string clears an open Needs-you item.
R3: GET /openapi.json on the FastAPI app returns 200.

## Acceptance criteria

R1 passes
