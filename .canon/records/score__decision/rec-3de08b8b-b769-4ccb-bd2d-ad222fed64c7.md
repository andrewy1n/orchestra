---
{
  "id": "rec-3de08b8b-b769-4ccb-bd2d-ad222fed64c7",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "move wheel smoke into web-packaging",
    "choice": "ci:wheel-smoke stays in the ci effort and web-packaging depends on it",
    "effort": "dashboard",
    "phase": "web-packaging"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-29T09:02:22+00:00",
  "relationships": {},
  "revision": "sha256:48d19fcfec2665d0ebc42d5222882c7f53028407bae8e1ef8303095e1f526fb1",
  "subject": "wheel-smoke-ownership"
}
---

## Rationale

There is no duplicate wheel job, and no change to another effort's plan.

## Counter-argument

web-packaging waits on a phase in another effort. Tools may not enforce a cross-effort order.
