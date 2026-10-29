---
{
  "id": "rec-3de470ae-01b3-4acd-b0cf-4f62ff0f3fb9",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "keep both servers",
    "choice": "Keep the FastAPI server and delete the stdlib server",
    "effort": "dashboard",
    "phase": "data-layer"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-29T09:02:15+00:00",
  "relationships": {},
  "revision": "sha256:b70b4800e7538bb072b953e0a76f9d357ade35d3dca1381e873270c5667d63d8",
  "subject": "one-fastapi-server"
}
---

## Rationale

Nothing in orchestra/ references the stdlib server. fastapi and uvicorn are main dependencies. Two servers double the route code and the tests.

## Counter-argument

The stdlib server needs no dependency, and an outside script may rely on it. This repo shows no such user, but an external one is possible.
