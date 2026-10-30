---
{
  "id": "rec-69a5b14b-d9df-4e50-a4df-85f6be82cbec",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "71408022fe817461a5699fe34a5e59fdd35826f1",
    "effort": "workflow-loop",
    "kind": "commands",
    "phase": "spec-analyze",
    "revision": "1ff226564c076a323592f035f5f34b0e59028443"
  },
  "record_type": "conductor:proof-packet",
  "recorded_at": "2026-10-29T16:52:25+00:00",
  "relationships": {},
  "revision": "sha256:9895c72b159bca30e7865dae8f6d334ebcb4461813f79be9289173d69cec3555",
  "subject": "spec-analyze"
}
---

## Look

A human runs `orchestra analyze` against a seeded store, once consistent and once with a missing acceptance, and checks exit 0 then exit 1 with the matching finding. On this phase's own records, `orchestra analyze spec-analyze --stage close --store <repo>/.canon` reports 0 errors and 9 warnings (all `compound-requirement`).

## Machine

- Specification rec-b171b4c5-13b3-4082-94f9-9eb681281fec (R1-R22), design rec-4c8c2000-2cb8-47c2-a866-12720022ae08.
- 6 work-items done; 26 active acceptances, 22 oracle-backed, every latest check-run is a runner pass at 1ff226564.
- 22 active assessments, all `verified`.
- Review check-run rec-0d63d62e-43ba-463b-bed2-b4fec02f0659 (pass at 1ff226564); integration-report rec-22bbe7c9-dcd3-4c60-adf9-3178c7acffed (pass).
- Types: `uv run basedpyright` 0 errors on the merged phase tree. Pytest at the phase tree: canon 268 passed, tuner 134 passed, tmux 20 passed (at 0b9737c4c, before one test-line change); orchestra tests 1495 passed at 1ff226564.
- No `.tuner/manifest.json`, so no verdict, trail, or audit.

## Attention

- The configured advisory suite check-run (`spec-analyze-suite`) was not recorded. The user chose to skip the re-run because the four pytest commands had already passed as listed above. The gate is `advisory`, so it does not block.
- `analyze` reports 9 compound-requirement warnings on this phase's own specification (R3-R7, R16, R19-R21). Some are truly non-atomic. Splitting them needs new oracles. Left for a follow-up.
- The approved plan had a dependency cycle (oracle tests drive `orchestra analyze`, which task 3 built). The subcommand was folded into `analyze-plan-checks`; the amendment is recorded. `analyze-cli` was left with README and CLI-surface pins.
- One planned oracle test (`test_r21_..._phase_end_order_names_the_analyze_stage`) demanded text R21 does not require and was removed before freezing.
- The full suite found an existing test that pinned the old phase-end order line. Fixed by `fix-order-line-test`.
- `main` advanced during the phase. `main` was merged into the phase branch once (0b9737c4c). It advanced again afterwards; the Landing merge takes those commits.
- `orchestra review-brief` is not scoped to a phase and ignores `--store` (loads the whole store, 2.4 MB). The reviewer brief for this phase was built with the same library function over this phase's records only.
- `--store` for `analyze` and `review-brief` takes the `.canon` directory, not the project root.

## Diff

```
README.md                                          |   1 +
 orchestra/cli.py                                   |  60 ++++
 orchestra/score/analyze.py                         | 126 ++++++++
 shared/ensure-store.md                             |   2 +
 skills/analyze-sessions/references/ensure-store.md |   2 +
 skills/engage/references/ensure-store.md           |   2 +
 skills/ensure-store.md                             |   2 +
 skills/execute-phase/SKILL.md                      |   2 +-
 skills/execute-phase/references/ensure-store.md    |   2 +
 skills/execute-phase/references/phase-end.md       |  13 +-
 skills/init/references/ensure-store.md             |   2 +
 skills/plan-phase/SKILL.md                         |   8 +
 skills/plan-phase/references/ensure-store.md       |   2 +
 skills/settle-phase/SKILL.md                       |  13 +-
 skills/settle-phase/references/ensure-store.md     |   2 +
 skills/triage-ideas/references/ensure-store.md     |   2 +
 skills/verify-work/references/ensure-store.md      |   2 +
 tests/test_analyze.py                              | 328 +++++++++++++++++++++
 tests/test_analyze_cli.py                          | 121 ++++++++
 tests/test_analyze_skills.py                       | 104 +++++++
 tests/test_cli_surface.py                          |   3 +-
 tests/test_tiered_verification.py                  |   2 +-
 22 files changed, 796 insertions(+), 5 deletions(-)
```
