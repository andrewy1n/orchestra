---
{
  "id": "rec-f4c4ed5f-880c-45db-a107-ee39eef85f8f",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "executor": "attest-core",
    "work_item": "attest-core"
  },
  "provenance": {
    "sources": [
      "attest-core"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T03:34:12+00:00",
  "relationships": {},
  "revision": "sha256:05f7c774b42ca7656346cc47ad35b17d698dd371a403482215ea21454d78df16",
  "subject": "attest-core",
  "time": {
    "observed": "2026-10-18T03:34:12+00:00",
    "recorded": "2026-10-18T03:34:12+00:00"
  }
}
---

## Orientation

Worktree: /home/andrewyin/affidavit--signed-verdict
Branch: phase/signed-verdict
Do not edit .artifacts or call adaptive-artifacts.
Frozen oracle (do not edit): tests/test_attestation.py

### Description
R1: Emit an SSH-signed attestation bound to commit, manifest hash, runner digest, and per-claim results.
R2: Verify rejects a bad signature under the allowlist.
R3: Verify rejects a well-signed attestation bound to a different commit or manifest hash.

### Approach
1. Add affidavit/attestation.py: canonical payload (namespace affidavit-verdict), sign via ssh-keygen -Y sign, verify via allowlist like amendments.
2. Extend aff CLI with attestation emit/verify (names at implementer choice: aff attest / aff attest-verify or subcommands).
3. Emit runs or accepts a verdict JSON and signs the bind fields.
4. Tests mint ed25519 keys like test_amendment; cover emit+verify pass, tamper fail, wrong commit/manifest fail.
5. Do not edit .github (attest-ci owns that).

### Requirements
R1: A command can emit an SSH-signed attestation of a verdict whose canonical payload includes the judged commit, the manifest hash, the runner digest, and per-claim results.
R2: A verify command rejects an attestation whose signature does not verify under the allowlist.
R3: A verify command rejects a well-signed attestation bound to a different commit or a different manifest hash than the one presented.

### Design Invariants
- Bad signature or wrong bind ⇒ non-zero verify.
- Distinct signing namespace from amendments.

### Design Assumptions
- frozen-environment has landed runner digest (or this phase digests runner argv the same way).
