---
{
  "id": "rec-ac0d1083-3a21-45f3-bdf8-bcaa944fbf3c",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "verdict-only affidavit; copy the trees and delete them later",
    "choice": "aff check, close-batch, and verdict stay in this repo; reviewer and suite move with the skills; the tier2 shim is deleted",
    "effort": "evidence-layer",
    "phase": "orchestration-split"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-17T07:28:57+00:00",
  "relationships": {
    "supersedes": [
      "rec-e0e79f7d-55c2-42ef-9b70-4d4a2225c3c3"
    ]
  },
  "revision": "sha256:1f58cf4c0ee6a452e781127ef7a054f7272d1dbb079739bad25232959f6e980d",
  "subject": "verb-home",
  "time": {
    "as_of": "2026-10-17T07:28:57+00:00"
  }
}
---

## Rationale

`evidence-kind` is the next phase of this effort, and its exit is a close refusal, so `aff close-batch` stays in this repo where that phase can extend it. The evidence-layer goal says an orchestration client gets gate answers through `aff` verbs, so `check`, `close-batch`, and `verdict` stay on `aff`. Reviewer and suite are the loop the skills import, so they move with the skills, the dashboard, and the session scripts. `affidavit/tier2.py` is a shim that re-exports `affidavit.suite`, and no skill or test imports it, so the shim and the `tier2_*` aliases in `suite.py` are deleted. `affidavit.aa` stops importing the dashboard before that tree leaves.

## Counter-argument

A verdict-only affidavit matches the standalone goal more closely. `check` and `close-batch` write the artifact store through adaptive-artifacts, so they behave as orchestration. Moving them would let this repo's tests import only the manifest and the verdict, and `evidence-kind` could become a verdict rule instead of a close rule.
