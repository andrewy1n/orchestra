---
{
  "id": "rec-cf3f4ea5-f382-4e16-b5cd-1808eafaeb1b",
  "lifecycle_state": "active",
  "payload": {
    "decisions": [
      "evidence-kind-enforcement"
    ],
    "effort": "evidence-layer",
    "phase": "evidence-kind"
  },
  "record_type": "score:design",
  "recorded_at": "2026-10-18T03:08:49+00:00",
  "relationships": {},
  "revision": "sha256:35de9a31b3cb7dfbc032e8906efa904a3ecaf4899866613fb1bccd396d3dcd66",
  "subject": "evidence-kind",
  "time": {
    "as_of": "2026-10-18T03:08:49+00:00"
  }
}
---

## Architecture

1. Add `evidence_kind` to claim parsing with enum validation.
2. Maintain an allowlist map kind → permitted runner templates (or template tags).
3. Before/during verdict, refuse claims whose active runner is not allowed for their kind.
4. Ship at least one interaction-oriented runner template and a fixture that uses it.

## Interfaces

- Claim field `evidence_kind`
- Template registry or tagged shipped templates
- Clear fail reason for kind mismatch

## Decisions

- `evidence-kind-enforcement`: field + template allowlist; not path-only; not pytest markers.

## Invariants

- Interaction cannot pass on default unit template.

## Assumptions

- Manifest still has one runner list; kind check compares that runner to the kind allowlist (per-claim runners remain out of scope unless plan-phase needs them).

## Tradeoffs

- Single manifest runner may force whole-repo interaction templates. Accept for now; per-claim runners are a later escape.

## Risks

- Flaky interaction fixtures. Mitigation: deterministic CLI e2e template in-repo.
