---
{
  "id": "rec-db47151b-fdd9-4bab-aeed-b37ce02f0e8b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "orchestra wrapper evidence-gate verb; encode policy as aff modes or check-run fields",
    "choice": "orchestra verify-work and execute-phase name when to record vs bind; aff stays mode-free",
    "effort": "evidence-layer",
    "phase": "evidence-workflow"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-18T09:29:16+00:00",
  "relationships": {},
  "revision": "sha256:4d89c3d11da332535f4b67ea81aeaf194a32cecae63439b5a323544dfdd07ced",
  "subject": "record-bind-policy-in-skills",
  "time": {
    "as_of": "2026-10-18T09:29:16+00:00"
  }
}
---

## Rationale

Record-versus-bind is agent policy, not a property of the evidence CLI. Encoding it as aff modes was already rejected: modes would grow a parallel work-kind taxonomy and tempt every technique to carry policy flags. Orchestra skills already own when to run gates; they are the right place to say when a trail row is enough and when a binding is required, while aff stays a mode-free verb surface.

## Counter-argument

An orchestra wrapper verb (one `evidence-gate` that trails and binds) would give agents a single command and reduce skill prose. That adds another CLI seam and hides the bind act inside a workflow helper, making it harder to see that earning is explicit — the opposite of the bind phase’s point.
