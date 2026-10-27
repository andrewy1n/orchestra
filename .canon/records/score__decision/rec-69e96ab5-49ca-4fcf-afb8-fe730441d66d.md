---
{
  "id": "rec-69e96ab5-49ca-4fcf-afb8-fe730441d66d",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Sigstore/OIDC identity; unsigned local advisory with CI-only gate",
    "choice": "SSH-sign a canonical verdict attestation (namespace affidavit-verdict) bound to commit, manifest hash, runner digest, and per-claim results; verify rejects tamper and wrong binds",
    "effort": "evidence-layer",
    "phase": "signed-verdict"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-18T03:08:48+00:00",
  "relationships": {},
  "revision": "sha256:2850540889d105ec2664255646b70c8e0916e2a4d4cd0c9cdebbfccbc8766407",
  "subject": "verdict-attestation",
  "time": {
    "as_of": "2026-10-18T03:08:48+00:00"
  }
}
---

## Rationale

Amendment signing already uses ssh-keygen and allowed_signers. Reusing that stack keeps one trust root and makes a merge gate verify bytes, not an agent-printed pass line.

## Counter-argument

Sigstore/OIDC would bind CI identity without managing deploy keys. It adds a new dependency and does not reuse the amendment allowlist the repo already ships.
