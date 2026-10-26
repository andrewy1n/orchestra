---
{
  "id": "rec-c30aaca7-94df-4c02-a6f3-fcce0c8d6b00",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "README Install matches manifests: single Claude marketplace add; Cursor does not claim dependency auto-install (exit criteria 2-3)",
    "effort": "packaging",
    "method": "check",
    "phase": "plugin-dep-marketplace",
    "requirement": "R4",
    "verify_command": "grep -q 'claude plugin marketplace add andrewy1n/se-workflow' README.md && grep -qi Cursor README.md && ! grep -qiE 'Cursor.*(auto-?install|plugin dependenc).*adaptive-artifacts' README.md"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-11T06:50:19+00:00",
  "relationships": {},
  "revision": "sha256:ef5bfdd37265682a4e977123ad1a9b2dbe51c5b3aa42e361b5546d82494e353d",
  "subject": "verify-plugin-dep-marketplace-readme",
  "time": {
    "as_of": "2026-10-11T06:50:19+00:00"
  }
}
---

