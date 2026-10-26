---
{
  "id": "rec-44ea8e19-d1e5-48af-b9d5-e927f9c3ca6b",
  "lifecycle_state": "superseded",
  "payload": {
    "criterion": "Loaded design for this repo has suite.mode=full and suite.gate=advisory and a command containing pytest tests",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "verification-policy",
    "requirement": "R6",
    "verify_command": "python3 -c \"import json; from pathlib import Path; d=json.loads(Path('contract/project-design.json').read_text()); s=d['phase_gate']['suite']; assert s['mode']=='full' and s['gate']=='advisory' and 'pytest' in s['command']\""
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-15T08:43:16+00:00",
  "relationships": {},
  "revision": "sha256:4ec3bfca43165dd121640caa9df001861e520e3bf3f811548ba355cf485f56fe",
  "subject": "phase-gate-contract-repo",
  "time": {
    "as_of": "2026-10-15T08:41:53+00:00"
  }
}
---

