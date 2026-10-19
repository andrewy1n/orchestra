---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-db3cca7b-c7b5-482b-be36-b59f59c5621b",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Exit 2: bin/se-workflow close-batch works through CLI; skills do not call scripts/close_batch.py",
    "effort": "packaging",
    "method": "tdd",
    "phase": "plugin-root-and-cli",
    "requirement": "R3",
    "verify_command": "uv run --with pytest python -m pytest tests/test_close_batch.py -q && grep -qE 'se-workflow close-batch|bin/se-workflow close-batch' skills/verify-work/SKILL.md && ! grep -q scripts/close_batch.py skills/verify-work/SKILL.md && uv run --with pytest python -m pytest tests/test_skill_contract_consistency.py -q"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-14T08:25:13+00:00",
  "relationships": {},
  "revision": "sha256:1a3c5167f56621334d450935548639bcf70075b17c51e568e4379a58ad874aa1",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verify-plugin-root-and-cli-close",
  "time": {
    "as_of": "2026-10-14T08:25:13+00:00"
  }
}
---

