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

R1 passes when a TestClient post of `{id, action: "dismiss"}` to `/api/backlog` returns 2xx and the open item is superseded to dismissed.
R2 passes when a TestClient post of a confirm body to `/api/needs` returns 2xx and the open item is cleared.
R3 passes when TestClient GET `/openapi.json` returns 200.

## Constraints

`fastapi` stays imported inside `create_app`. `dashboard-human-gate-writes` still limits store writes to Needs-you gates and backlog promote/dismiss.

## Non-goals

Changing how the page formats a FastAPI `detail` validation error. Changing the stdlib server in `dashboard/web/service.py`.

## Invariants

POST `/api/backlog` and POST `/api/needs` still call `Reader.write_backlog` and `Reader.write_needs`. No new store write path.

## Assumptions

Removing `from __future__ import annotations` from `dashboard/web/app.py` evaluates `Request`, `JSONResponse`, and `HTMLResponse` in `create_app`'s local scope. Importing `dashboard.web.app` still does not import `fastapi`.
