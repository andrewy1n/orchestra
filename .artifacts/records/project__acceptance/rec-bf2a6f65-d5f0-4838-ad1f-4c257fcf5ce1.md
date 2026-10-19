---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-bf2a6f65-d5f0-4838-ad1f-4c257fcf5ce1",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Bundled contract phase_gate.suite is mode=none empty command; live .artifacts/project-design.json is full+advisory with pytest in command; tests assert both from real JSON (not only a local constant)",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "verification-policy",
    "requirement": "R2",
    "verify_command": "uv run --with pytest python -m pytest tests/test_contract_self_consistency.py -q -k phase_gate && python3 -c \"import json; from pathlib import Path; b=json.loads(Path('contract/project-design.json').read_text())['phase_gate']['suite']; assert b['mode']=='none' and b.get('command','')==''; a=json.loads(Path('.artifacts/project-design.json').read_text())['phase_gate']['suite']; assert a['mode']=='full' and a['gate']=='advisory' and 'pytest' in a['command']\""
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-15T09:15:40+00:00",
  "relationships": {},
  "revision": "sha256:a9d23d11f11ab621098d27f79282365252bd393eee2858f86f51e8880dc86364",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "fix-phase-gate-defaults",
  "time": {
    "as_of": "2026-10-15T09:15:40+00:00"
  }
}
---

