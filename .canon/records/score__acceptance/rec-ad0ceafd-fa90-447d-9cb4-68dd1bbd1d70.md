---
{
  "id": "rec-ad0ceafd-fa90-447d-9cb4-68dd1bbd1d70",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "phase-level",
    "requirement": "R9",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/phaseLeaf.test.ts -t \"R9 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=1 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T19:03:43+00:00",
  "relationships": {},
  "revision": "sha256:25f80b3c05f56a8caf46c1e07fe86695545277276e3a780cc506744c4ab6710d",
  "subject": "leaf-over-page"
}
---

