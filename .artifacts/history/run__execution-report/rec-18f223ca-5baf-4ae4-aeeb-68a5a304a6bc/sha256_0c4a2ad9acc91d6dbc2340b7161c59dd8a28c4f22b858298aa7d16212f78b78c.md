---
{
  "id": "rec-18f223ca-5baf-4ae4-aeeb-68a5a304a6bc",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "store-client",
    "result": "pass",
    "revision": "5a9b02fe2f6c7aaff17f304ed1ad1e065b834538",
    "verdict": "pass",
    "work_item": "store-client"
  },
  "provenance": {
    "sources": [
      "store-client"
    ]
  },
  "record_type": "run:execution-report",
  "recorded_at": "2026-10-21T10:22:29+00:00",
  "relationships": {},
  "revision": "sha256:0c4a2ad9acc91d6dbc2340b7161c59dd8a28c4f22b858298aa7d16212f78b78c",
  "subject": "store-client",
  "time": {
    "observed": "2026-10-21T10:22:29+00:00",
    "recorded": "2026-10-21T10:22:29+00:00"
  }
}
---

subject: store-client
kind: deliver
result: pass
revision: 5a9b02fe2f6c7aaff17f304ed1ad1e065b834538
evidence: python3 -m pytest tests/test_store_client.py tests/test_store_client_layout.py tests/test_verdict_gate.py -q --tb=line → 10 passed. observation.record_observation and binding.bind_observation call Project.create; observation.list_observations and binding.list_bindings call Project.list via open_store. Subprocess clients removed. test_no_store_tokens no longer rejects adaptive-artifacts or project:. R5 still fails if an affidavit module starts adaptive-artifacts. Frozen hashes unchanged (test_store_client.py 39790bc3eec3954dfd957db28be1875d382ee304e08ba04dceb3dcd884c2da43, test_store_client_layout.py f62f1454d1e08cd5fec4ed1e7e58e709c9e899d407fa7be579ee186ab3fcdef5).
observations: A missing resolved contract still skips observation recording before open_store. unbind retires a binding through Project.apply. adaptive-artifacts 0.1.0 from the aa-library worktree was installed into user site-packages so aff subprocesses can import it after PYTHONPATH is stripped.
root_cause:
verdict: pass
metrics: 10 passed
claim: observation and binding call Project.create and Project.list, and no affidavit module starts adaptive-artifacts.
needs_human: false
attempted_action:
retry_when:
blocker:
