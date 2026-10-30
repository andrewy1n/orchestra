---
{
  "id": "rec-e94ef1b8-79da-4bdf-bec0-5aa144fe5b17",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "overlay.svelte.ts linkCtx takes the phase from routePhase only, which is null on those routes; links.ts returns null for a requirement ref without a phase",
    "claim": "behavior-bug on effort-phase-rows: bare R<n> ids in claim text stop linking on the effort page and in the needs, backlog and record modals",
    "effort": "dashboard",
    "invalidated_when": "fix lands and reviewer re-run passes, or human clears",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-30T19:53:48+00:00",
  "relationships": {},
  "revision": "sha256:c82c0aaf2ea34d727f1a89d29517330d6df56ff95e94b7a58ddf7fe6ea32f142",
  "subject": "review-effort-phase-rows-behavior-bug"
}
---

## Evidence

Expected: the effort page and the needs, backlog and record modals keep resolving bare requirement ids in claim text, as before the phase. Observed: overlay.svelte.ts:37-47 gives linkCtx.phase null on those routes, and links.ts:75-77 then returns null for a requirement ref.

## Consequence

Phase merge is blocked until the finding is fixed or cleared. The loss is small: plain text where a link used to be.

## Follow-up

Fix task fix-link-context restores the default phase as the fallback phase of the link context.
