---
{
  "id": "rec-206dc7a5-a4a7-4e2e-ad14-8c28cab7ed68",
  "lifecycle_state": "done",
  "payload": {
    "effort": "evidence-layer",
    "ordinal": 10,
    "title": "aff audit: changed code no witness checks"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-18T04:20:19+00:00",
  "relationships": {},
  "revision": "sha256:4e61582f14aaad5c856aef70d593625d5010ef86df2d4deb2ccca6e15f93ce27",
  "subject": "phase-end-evidence"
}
---

## Problem

Tests can be blind to code they execute. A claim's witness can pass at head while a changed block, or a small bug in it, goes unnoticed.

## Approach

Adopt `audit-hunk-mutants`: `aff audit --base --head` productizes hunk-revert + capped mutants, judges with frozen claim tests via `run_tests`, advisory JSON, never reports test-file blocks. Phase-end reviewer skipped.

## Exit criteria

- On the check-runner range, reports the unnoticed cwd block and at least one surviving mutant from the spike findings.
- Never reports a test-file block.

## Landing

- **branch:** `phase/phase-end-evidence`
- **worktree:** `/home/andrewyin/affidavit--phase-end-evidence`
- **base:** `main`
- **close:** commit code on the phase branch; merge that branch into `main`; commit the store on the primary checkout
- **push:** not a stop (do not push)

## Run

One sitting. No human stops. Wave 1 is `audit-blocks` (`subagent`, 25 minutes, R1-R3). Wave 2 is `audit-mutants` (`subagent`, 15, R4), which depends on `audit-blocks`. Wave 3 is `verify-phase-end-evidence` (`inline`, 6). Phase elapsed is 46 minutes.

Collision notes: the two tasks run in sequence and share `affidavit/audit.py` and `affidavit/cli.py`; `audit-blocks` owns block splitting, revert, and labeling, `audit-mutants` adds mutant planting on top. `tests/test_audit.py` is frozen.

Range note: the spike data in `spikes/hunk-revert/results-phase-a.json` places the unnoticed `build_batch(request, cwd=args.cwd)` hunk (`scripts/close_batch.py:326`, `should_be_tested`) in the red-first range `b3159b6..c14dedb`, not in the check-runner range `3b5ce10..4bd42b9`. The requirement text says check-runner; the oracle uses the range that actually holds the block. Plan-review answered at once under the campaign pre-approval.
