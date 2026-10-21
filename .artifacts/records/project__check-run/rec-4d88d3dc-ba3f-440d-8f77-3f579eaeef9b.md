---
{
  "base_kind": "event",
  "id": "rec-4d88d3dc-ba3f-440d-8f77-3f579eaeef9b",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-89843013-38fa-4ad0-af4f-aceb43c5232e",
    "duration_s": 0.664171,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_orchestra_callers.py::test_r1\"]",
    "method": "tdd",
    "output_sha256": "18d1a850fd41213ce7450924eb821c66331b1a4629c466e54bf031bb37eeefc1",
    "requirement": "R1",
    "result": "fail",
    "revision": "cdcb9861c1b7f82caf097b00472d16f902d8d5b9",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "replace-resolvers"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T10:43:55+00:00",
  "relationships": {
    "informed_by": [
      "rec-89843013-38fa-4ad0-af4f-aceb43c5232e"
    ]
  },
  "revision": "sha256:6f104dcf0d8fd766d565dc0c67d84e02f543d55d5da5525b7b73e85e57cff246",
  "subject": "replace-resolvers",
  "time": {
    "observed": "2026-10-21T10:43:55+00:00",
    "recorded": "2026-10-21T10:43:55+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________________________ test_r1 ____________________________________

    def test_r1():
        """R1: modules under orchestra/ open the store with adaptive_artifacts.project.open_store."""
        offenders, callers = _store_access(ROOT / "orchestra")
>       assert not offenders, "orchestra opens the store another way: " + "; ".join(offenders)
E       AssertionError: orchestra opens the store another way: orchestra/_scripts/record_reader.py:73: command adaptive-artifacts; orchestra/aa.py:10: from orchestra.aa_resolve import; orchestra/aa.py:41: resolve_aa_command; orchestra/aa.py:45: command adaptive-artifacts; orchestra/aa_resolve.py:64: def resolve_aa_command; orchestra/aa_resolve.py:97: store binding resolution; orchestra/aa_resolve.py:98: store binding resolution; orchestra/aa_resolve.py:99: store binding resolution; orchestra/aa_resolve.py:84: command adaptive-artifacts; orchestra/aa_resolve.py:76: command artifacts.py; orchestra/aa_resolve.py:47: command adaptive-artifacts; orchestra/aa_resolve.py:48: command artifacts.py; orchestra/aa_resolve.py:49: command adaptive-artifacts; orchestra/aa_resolve.py:50: command artifacts.py; orchestra/aa_resolve.py:49: command adaptive-artifacts; orchestra/aa_resolve.py:50: command adaptive-artifacts; orchestra/check.py:14: from orchestra import aa; orchestra/cli.py:11: from orchestra import aa; orchestra/cli.py:12: from orchestra.aa_resolve import; orchestra/close_batch.py:48: from orchestra import aa; orchestra/suite.py:22: from orchestra import aa; orchestra/suite.py:148: from orchestra.aa_resolve import
E       assert not ['orchestra/_scripts/record_reader.py:73: command adaptive-artifacts', 'orchestra/aa.py:10: from orchestra.aa_resolve ...ts', 'orchestra/aa_resolve.py:64: def resolve_aa_command', 'orchestra/aa_resolve.py:97: store binding resolution', ...]

tests/test_orchestra_callers.py:391: AssertionError
=========================== short test summary info ============================
FAILED tests/test_orchestra_callers.py::test_r1 - AssertionError: orchestra o...
1 failed in 0.14s
