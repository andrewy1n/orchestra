---
{
  "base_kind": "observation",
  "id": "rec-fa3dc511-e18b-42da-80a0-deda63d3cdd4",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "library-fixture",
    "result": "pass",
    "revision": "b624a3dcb27c119bdc37b928025d33959e9da77d",
    "verdict": "pass",
    "work_item": "library-fixture"
  },
  "provenance": {
    "sources": [
      "library-fixture"
    ]
  },
  "record_type": "project:execution-report",
  "recorded_at": "2026-10-21T12:14:54+00:00",
  "relationships": {},
  "revision": "sha256:8eb2223a3454d853ee94d96af635f22b9c0c04dd67a33074e3986d36d5c40355",
  "subject": "library-fixture",
  "time": {
    "observed": "2026-10-21T12:14:54+00:00",
    "recorded": "2026-10-21T12:14:54+00:00"
  }
}
---

subject: library-fixture
kind: deliver
result: pass
revision: b624a3dcb27c119bdc37b928025d33959e9da77d
evidence: PATH="$(pwd)/bin:$PATH" python3 -m pytest tests/test_library_e2e.py::test_library_fixture_close -q → 1 passed in 0.38s. R1, R2, R3, R4, and R6 method checks re-run, each exit 0. tests/test_library_e2e.py sha256 unchanged (0ef313605d4aac90449c3a5c80be66aeceb1b9206e87c0c458ef522526c6c5b4).
observations: close-batch exited 2 with "affidavit recheck refused for claim 'claim-widget': unknown record type: 'project:evidence-binding'". The fixture store is initialized from contract/project-design.json, which did not declare that type, so the fixture bind was swallowed and recheck could not list bindings. Added project:evidence-binding (current-status; observation_id, claim_id, base_rev, head_rev, optional effort) to that contract. Command close then exits 0; in-process close still does not start aff or adaptive-artifacts.
root_cause: Orchestra's bundled project design omitted project:evidence-binding, so the claim gate's in-process recheck refused a close the fixture had otherwise prepared.
verdict: pass
metrics: pytest 1 passed in 0.38s; contract/project-design.json +18 lines
claim: orchestra close-batch exits 0 on the generated fixture for a close that meets the claim gate.
needs_human: false
attempted_action:
retry_when:
blocker:
