---
{
  "id": "rec-e2ebbb00-cf85-46ff-bd83-0d3aacc15a82",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "phase-level",
    "requirement": "R25",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/linkContext.test.ts -t \"R25 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=2 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T19:53:49+00:00",
  "relationships": {},
  "revision": "sha256:fc8c65e4377b8b902c24d7299830bae0988bba9d0c5244d2f179f209e42751f0",
  "subject": "fix-link-context"
}
---

