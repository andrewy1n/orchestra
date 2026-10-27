---
{
  "id": "rec-ec2a17c7-ada2-4c03-ba16-b0392baa8ea9",
  "lifecycle_state": "done",
  "payload": {
    "effort": "evidence-layer",
    "ordinal": 7,
    "title": "Verdict checks who wrote the oracle and when"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-18T03:45:35+00:00",
  "relationships": {},
  "revision": "sha256:da23ce79fcff5b62fd0e727cdbda4e988e6ce85e68ae80e9f9d2f174777e0470",
  "subject": "oracle-provenance"
}
---

## Problem

The core guarantee is that the test author is not the agent that benefits from a pass. Today orchestra keeps that by process. A standalone user gets nothing that enforces it.

## Approach

Adopt `oracle-provenance-check`: verdict uses git for oracle-before-impl ordering, oracle/support-only paths on the oracle commit, and different SSH commit signers when history is signed. Phase-end reviewer skipped.

## Exit criteria

- Fail fixtures for oracle-after-impl, oracle touching source, and shared signer.
- Pass fixture that meets all three.

## Landing

- **branch:** `phase/oracle-provenance`
- **worktree:** `/home/andrewyin/affidavit--oracle-provenance`
- **base:** `main`
- **close:** commit code on the phase branch; merge that branch into `main`; commit the store on the primary checkout
- **push:** not a stop (do not push)

## Run

One sitting. No human stops. Every task is `subagent`.

Single wave: `provenance-check` (25 minutes) owns `affidavit/provenance.py`, the `aff verdict` wiring in `affidavit/verdict.py` and `affidavit/cli.py`, and `tests/test_provenance.py` is frozen. Wave 2 is `verify-oracle-provenance` (8). Phase elapsed is 33 minutes.

Collision notes: only one implementation task, so no shared areas. Provenance is evaluated only with `aff verdict --provenance` so existing verdict fixtures stay unchanged. Plan-review answered at once under the campaign pre-approval.
