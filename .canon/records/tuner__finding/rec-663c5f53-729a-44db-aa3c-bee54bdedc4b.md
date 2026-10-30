---
{
  "id": "rec-663c5f53-729a-44db-aa3c-bee54bdedc4b",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "Journal Back, the Esc handler in App.svelte and closeDetail's empty-stack fallback use openHash(\"\"). Before this phase that was the effort Home. After opening a #/task or #/phase deep link, closing lands on the product index and the effort context is lost. No test covers it.",
    "claim": "behavior-bug on phase: closing a detail overlay or the journal with no in-app history, and Esc, call openHash(\"\") which now opens the product index instead of the effort page",
    "effort": "dashboard",
    "invalidated_when": "fix lands and reviewer re-run passes, or human clears",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-30T08:42:09+00:00",
  "relationships": {},
  "revision": "sha256:05a75a7cbb603f4ae4ead5963fe7c540c24312934b5f00b357539092a7b6771c",
  "subject": "review-area-levels-close-fallback"
}
---

## Evidence

Journal Back, the Esc handler in App.svelte and closeDetail's empty-stack fallback use openHash(""). Before this phase that was the effort Home. After opening a #/task or #/phase deep link, closing lands on the product index and the effort context is lost. No test covers it.

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Fix task fix-area-levels-review sends these fallbacks to the effort page.
