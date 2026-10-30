---
{
  "id": "rec-ac8ce292-05bb-402b-9df9-3e9cfe5085da",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "phase": "area-levels",
    "requirement": "R23",
    "verify_command": "cd dashboard/frontend && f=$(mktemp) && npx vitest run src/lib/screens/breadcrumbRail.test.ts -t \"R23 \" --reporter=json --outputFile=$f >/dev/null 2>&1; jq -e \".numPassedTests>=1 and .numFailedTests==0\" $f"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T08:00:26+00:00",
  "relationships": {},
  "revision": "sha256:b7f5da9a7df9aa68a8f3606ccc66c22706ce09683ebe9e01c618a4d6c3d26a90",
  "subject": "breadcrumb-rail-r23"
}
---

