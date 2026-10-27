---
{
  "id": "rec-68cb1a7b-9f22-4372-88e3-2cf81ecafddd",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-282b9531-ae72-4d08-bb9e-3b90139f7561",
    "diff_sha256": "b8dc76121db6374240f8f7161f52b6ec2b14ab902d5f27d47c15f14815887e7c",
    "duration_s": 0.573042,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_audit_probes.py::test_r1_audit_runs_declared_probes_at_base_and_head"
    ],
    "informed_by": [
      "rec-282b9531-ae72-4d08-bb9e-3b90139f7561"
    ],
    "method": "tdd",
    "output_sha256": "2565c01deab9a1220ace8fd5a16f14e267d906f8428d16f493677972490f0381",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "audit-probes"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T04:23:23+00:00",
  "relationships": {},
  "revision": "sha256:2ae586548f953cb8018e289e2215b16567e4386dcaceac0cb150a39a6c5963d8",
  "subject": "audit-probes",
  "time": {
    "observed": "2026-10-18T04:23:23+00:00",
    "recorded": "2026-10-18T04:23:23+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________ test_r1_audit_runs_declared_probes_at_base_and_head ______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-332/test_r1_audit_runs_declared_pr0')

    def test_r1_audit_runs_declared_probes_at_base_and_head(tmp_path: Path):
        """R1: aff audit runs declared probes at base and at head and compares results."""
        root = tmp_path / "repo"
        _init(root)
        _write(
            root,
            {
                "pytest.ini": PYTEST_INI,
                "app.py": BASE_APP,
                ".affidavit/probes.json": json.dumps(PROBE_CLI, indent=2) + "\n",
            },
        )
        base = _commit(root, "base")
        _write(root, {"app.py": HEAD_APP})
        head = _commit(root, "head")
        payload = _payload(_audit(root, base, head))
>       assert "diffs" in payload
E       AssertionError: assert 'diffs' in {'advisory': True, 'base': 'eef655dc75bccff35a98d6c717847bfed07cc062', 'blocks': [{'end': 1, 'file': 'app.py', 'label': 'inconclusive', 'start': 1, ...}], 'head': '8a11145f3edadce8960527b81b1efa37ae8563af', ...}

tests/test_audit_probes.py:111: AssertionError
=========================== short test summary info ============================
FAILED tests/test_audit_probes.py::test_r1_audit_runs_declared_probes_at_base_and_head
1 failed in 0.12s
