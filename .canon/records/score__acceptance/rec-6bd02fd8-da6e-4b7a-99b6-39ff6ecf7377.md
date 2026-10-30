---
{
  "id": "rec-6bd02fd8-da6e-4b7a-99b6-39ff6ecf7377",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "check",
    "phase": "web-packaging",
    "requirement": "R10",
    "verify_command": "id=$(gh run list --workflow ci.yml --limit 30 --json databaseId,headBranch,event,headSha --jq '[.[] | select(.headBranch==\"phase/web-packaging\" and .event==\"push\" and .headSha==\"'\"$(git rev-parse HEAD)\"'\")][0].databaseId') && gh api repos/{owner}/{repo}/actions/runs/$id --jq .conclusion | grep -qx success"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T01:01:49+00:00",
  "relationships": {},
  "revision": "sha256:378818a8271bade3a84d714c42adf9b6251a21dfbbe355e246ae0ed85ba1896e",
  "subject": "verify-web-packaging-ci"
}
---

