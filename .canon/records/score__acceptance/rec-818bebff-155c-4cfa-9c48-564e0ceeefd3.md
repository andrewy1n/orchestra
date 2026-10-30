---
{
  "id": "rec-818bebff-155c-4cfa-9c48-564e0ceeefd3",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "phase-level",
    "requirement": "R6",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/phasePage.test.ts -t \"R6 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=1 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T19:03:31+00:00",
  "relationships": {},
  "revision": "sha256:22b9f9f42734f376c032ddee863abf5f9662639f4a8a1add66d026845f44bec0",
  "subject": "phase-page-r6"
}
---

