---
{
  "id": "rec-a7b9abb6-641f-4aed-9eb5-794cf1fdf537",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "area-levels",
    "requirement": "R13",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/startedChip.test.ts -t \"R13 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=1 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T08:00:41+00:00",
  "relationships": {},
  "revision": "sha256:1fc141428124d835c0bd300af03185085ea096327f0006b01818307c63077543",
  "subject": "area-chip-started-r13"
}
---

