---
{
  "id": "rec-22bbe7c9-dcd3-4c60-adf9-3178c7acffed",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "phase": "spec-analyze",
    "result": "pass",
    "revision": "1ff226564c076a323592f035f5f34b0e59028443"
  },
  "record_type": "conductor:integration-report",
  "recorded_at": "2026-10-29T08:47:18+00:00",
  "relationships": {},
  "revision": "sha256:6ec61efeeabe016c9fe954139983b9f1fa5c2e48d01e8c4a9c07b91cd7bf61f1",
  "subject": "spec-analyze"
}
---

## Interfaces

`orchestra/score/analyze.py` exposes `analyze_phase(records, phase, stage="plan")` returning a `Report` (`phase`, `stage`, `skipped`, `findings`, `ok`) of `Finding` (`severity`, `code`, `subject`, `message`). `orchestra analyze <phase> [--stage plan|close] [--json] [--cwd] [--store]` exits 0, 1, or 2. Skills settle-phase, plan-phase, and execute-phase (SKILL.md and references/phase-end.md) name the command and its refusal rule. README, tests/test_cli_surface.py, and the ensure-store copies list `analyze`.

## Assumptions

`## Requirements` lines are `Rn: text`, one per line. A phase has one active specification and one active design. Phase records match by `payload.phase`. Check-runs match an acceptance by `criterion_id`, and the latest by `recorded_at` counts.

## Invariants

Exit 1 if and only if an error finding exists. No write to the store or disk. The same store and arguments give the same output. Withdrawn work-items and superseded records are never counted. `orchestra/score/` imports only canon.

## Conflicts

None within the phase. The reviewer saw AGENTS.md and CLAUDE.md hunks in `git diff main..HEAD` that come from a later `main` commit (bc9a1f089), not from phase work.
