---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-493c2b46-eefa-4ce6-bf54-c5e2bdbd6ec9",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "decisions": "phase-reviewer-scope,reviewer-inputs",
    "effort": "workflow-loop",
    "phase": "phase-reviewer"
  },
  "record_type": "project:design",
  "recorded_at": "2026-10-11T06:26:06+00:00",
  "relationships": {},
  "revision": "sha256:a8bbd887442a2510567bef097f833aa4ed65277835a613cbae3bac8154c9a9c2",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "phase-reviewer",
  "time": {
    "as_of": "2026-10-11T06:26:06+00:00"
  }
}
---

## Architecture

At phase end, after the closing verification task succeeds once, the parent dispatches a read-only reviewer subagent from `agents/se-reviewer.md` (Cursor: documented equivalent with the tightest tool restriction available). The brief contains only work-item titles/descriptions/Approach goals, acceptances, structured requirements/invariants, and `git diff <base>..<phase-head>` plus read access to the tree. It must not include execution reports, check-runs, assessments, or assignment notes.

The reviewer returns structured output:

```
verdict: PASS | NEEDS_WORK
findings: [{ task, kind, expected, observed, severity }, ...]
integration: { interfaces, assumptions, invariants, conflicts }
```

Parent writes: one `method: review` / `evidence_kind: review` check-run at the phase head; one finding per NEEDS_WORK item (`needs: none` when a fix task is created, `needs: human` for judgment calls). Fixable findings become fix work-items via retry-loop; verification/`depends_on` re-gating applies as designed there. After fixes, reviewer runs once more. Phase gate requires a passing review check-run at head before merge (and before tier-2 later). Parent writes the integration-report body from the reviewer's integration section.

Out of scope: per-task review flag, pre-dispatch coverage check.

## Interfaces

- Plugin file: `agents/se-reviewer.md` (tools: Read, Grep, Glob, Bash; no Write/Edit; prompt forbids mutating commands).
- execute-phase: phase-end step order; brief construction; parent record writes; fix-task handoff; one re-run; gate check.
- verify-work / close: unchanged for ordinary tasks; review check-run is phase-level evidence.
- Tests: brief exclusion, `status-tabs` fixture, skill↔contract consistency.

## Decisions

- phase-reviewer-scope: phase-end core; defer per-task review and pre-dispatch coverage
- reviewer-inputs: specs + acceptances + invariants + phase diff only; no builder self-grades

## Invariants

- Reviewer writes no store records.
- Single writer remains the parent.
- `done` tasks are not reopened; gaps are new fix tasks.

## Assumptions

- Host supports tool restriction for the reviewer agent; if Cursor cannot match Claude Code `agents/`, the skill documents the fallback and still forbids writes in the prompt.
- retry-loop fix-task and budget machinery is available when this phase executes (ordinal after retry-loop).

## Tradeoffs

- Phase-end only vs full #10: later catch for plan gaps; smaller phase.
- Restricted inputs vs full context: more false positives possible; independence preserved.

## Risks

- Cursor cannot hard-block Write/Edit — mitigate with prompt + parent refusing reviewer-authored store ops; prefer Claude Code agent file when available.
- Noisy NEEDS_WORK — severity + human `needs: human` for judgment calls; budget stops infinite fix loops.
