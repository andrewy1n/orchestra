---
{
  "id": "rec-1fb19def-2915-4ba6-b0d3-95fc67acce89",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "area-levels",
    "requirement": "R2",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/productIndex.test.ts -t \"R2 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=1 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T08:00:29+00:00",
  "relationships": {},
  "revision": "sha256:3da81098a63c608a1f0c70f70e5dd0518e3fff4a3ff2f36dea4f58d8963f1bec",
  "subject": "product-index-r2"
}
---

