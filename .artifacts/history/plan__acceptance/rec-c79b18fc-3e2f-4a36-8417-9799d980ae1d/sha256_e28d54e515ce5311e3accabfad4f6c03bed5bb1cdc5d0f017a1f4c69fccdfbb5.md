---
{
  "id": "rec-c79b18fc-3e2f-4a36-8417-9799d980ae1d",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "acceptance.criterion is optional; brief/plan/verification acceptance roles do not list criterion in requires_payload",
    "effort": "workflow-loop",
    "method": "check",
    "phase": "atomic-claims",
    "requirement": "R4",
    "verify_command": "python3 -c \"import json; from pathlib import Path; d=json.loads(Path('contract/project-design.json').read_text()); acc=next(r for r in d['records'] if r['name']=='acceptance'); assert 'criterion' in acc['optional_payload']; req=set(acc['payload'])-set(acc['optional_payload']); assert 'criterion' not in req; views=d['views'] if isinstance(d['views'],dict) else {v['id']:v for v in d['views']};\n\""
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-16T19:11:17+00:00",
  "relationships": {},
  "revision": "sha256:e28d54e515ce5311e3accabfad4f6c03bed5bb1cdc5d0f017a1f4c69fccdfbb5",
  "subject": "contract-thin-criterion",
  "time": {
    "as_of": "2026-10-16T19:10:56+00:00"
  }
}
---

