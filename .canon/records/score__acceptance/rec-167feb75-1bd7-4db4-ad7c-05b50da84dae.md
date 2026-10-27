---
{
  "id": "rec-167feb75-1bd7-4db4-ad7c-05b50da84dae",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "execute-phase and verify-work run aff verdict for a claim in the manifest and treat a non-zero exit as not done",
    "effort": "evidence-layer",
    "method": "tdd",
    "phase": "orchestration-split",
    "requirement": "R6",
    "verify_command": "cd ~/orchestra && python3 -m pytest tests/test_skill_evidence_boundary.py -q -k verdict"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-17T07:38:12+00:00",
  "relationships": {},
  "revision": "sha256:79b7a30446b889f29ccd79823346831cc69994bffbac18f779eecb55e354db81",
  "subject": "verify-orchestration-split-verdict",
  "time": {
    "as_of": "2026-10-17T07:38:12+00:00"
  }
}
---

