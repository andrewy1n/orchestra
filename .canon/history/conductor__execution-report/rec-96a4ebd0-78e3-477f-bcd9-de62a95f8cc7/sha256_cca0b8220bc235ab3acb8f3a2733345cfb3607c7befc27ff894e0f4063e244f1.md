---
{
  "id": "rec-96a4ebd0-78e3-477f-bcd9-de62a95f8cc7",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "store-module",
    "result": "pass",
    "revision": "8141ca825c3b3d0cca44c35c8df86bbcb0114dc3",
    "verdict": "pass",
    "work_item": "store-module"
  },
  "record_type": "conductor:execution-report",
  "recorded_at": "2026-10-29T20:59:52+00:00",
  "relationships": {},
  "revision": "sha256:cca0b8220bc235ab3acb8f3a2733345cfb3607c7befc27ff894e0f4063e244f1",
  "subject": "store-module"
}
---

subject: store-module
kind: deliver
result: pass
revision: 8141ca825c3b3d0cca44c35c8df86bbcb0114dc3
evidence: New dashboard/backend/store.py: Record, ModelError, change_token, pinned_token, declared_record_types, stored_record (raw Project.get), get_record (stored record plus derived values), list_records (filters type, state, subject prefix, payload equality in typed Python), and the catalog cache moved from model.py. It is the only module calling Project.get; nothing calls Project.list (the old _run read Project.records() plus derived() through the catalog, now in store._catalog). model.py lost _options, _run, _catalog, _pinned_token, _declared_record_types and change_token; its 3 + 1 _run calls in load_task_detail and load_phase_detail now use store.get_record and store.list_records; journal.py load_record uses store.get_record; dismiss.py and approval.py use store.stored_record; server/service.py uses store.change_token. tests/test_dashboard_model.py retargeted 6 monkeypatching tests. Checks: test_data_layer -k "r1 or r2" r1 and r2 pass (r10 fails, out of scope); endpoint shapes, model, journal: 143 passed; web, gates, status, idea, proof: 36 passed; basedpyright 0 errors; ruff clean.
observations: The payload filter compares plain strings; the old --where parser JSON-coerced values; callers only filter on effort and phase slugs. FULL_TYPES stays in model.py because tests/test_proof_dashboard.py reads it.
needs_human: false
