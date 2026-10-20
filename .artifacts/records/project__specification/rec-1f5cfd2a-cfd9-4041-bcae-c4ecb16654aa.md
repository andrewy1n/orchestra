---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-1f5cfd2a-cfd9-4041-bcae-c4ecb16654aa",
  "identity": "unknown",
  "lifecycle_state": "superseded",
  "payload": {
    "effort": "dashboard",
    "phase": "phase-overview",
    "requirements": "R1,R2,R3,R4,R5,R6,R7,R8",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-20T04:46:57+00:00",
  "relationships": {},
  "revision": "sha256:e5342ee91cb104008a75f733dcea5c9efa76354ab0e837aba56ff64353f12337",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "phase-overview",
  "time": {
    "as_of": "2026-10-20T03:10:50+00:00"
  }
}
---

## Requirements

R1: The phase overlay Overview tab shows status chips including lifecycle state and task done/total (and awaiting sign-off when set).
R2: Overview shows a progress cue for the phase's tasks (done/total or equivalent).
R3: Overview shows a next-action line derived from existing dashboard next-step or position cues when available, otherwise a short fallback.
R4: When the phase has requirements/evidence, Overview shows one clickable glyph or chip per requirement reflecting status.
R5: Activating a requirement control on Overview opens the requirement overlay for that id.
R6: Overview shows a compact per-wave summary of tasks in that phase (counts or glyphs by wave).
R7: Spec, Design, Decisions, Evidence, Tasks, and Proof tabs keep their existing roles and are not replaced by Overview.
R8: A phase with no specification still gets the structured Overview chrome; missing blocks show empty states rather than raw JSON.

## Acceptance criteria

- UI tests render Overview with chips, requirements strip (seeded), and wave summary without dumping the phase body as the sole content.
- Clicking a requirement chip opens the requirement overlay.
- `npm test` passes for those cases.
- Manual: open an in-progress structured phase and confirm Overview is scannable before reading spec prose.

## Constraints

- Prefer data already on GET /api/phase (detail, evidence, tasks); avoid new endpoints unless a field is missing.
- Do not change Textual in this phase.
- Task dependency graph is out of scope (phase `task-graph`).

## Non-goals

- Redesigning Spec/Design markdown rendering.
- Journal or home-rail changes.
- Editing phase fields from Overview.

## Invariants

- Phase tab set still comes from `tabs_for`.
- Esc closes the phase overlay.

## Assumptions

- Requirement status glyphs can follow the spike/TUI vocabulary already used in evidence views.
