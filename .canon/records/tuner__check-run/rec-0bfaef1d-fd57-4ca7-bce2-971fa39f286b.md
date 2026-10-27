---
{
  "id": "rec-0bfaef1d-fd57-4ca7-bce2-971fa39f286b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-841b4a3f-f2d6-40c0-b73f-b4af1186f1e8",
    "duration_s": 0.527742,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_audit_probes.py::test_r2_audit_reports_unclaimed_probe_difference"
    ],
    "informed_by": [
      "rec-841b4a3f-f2d6-40c0-b73f-b4af1186f1e8"
    ],
    "method": "tdd",
    "output_sha256": "da0cd996faf73001d01eac017242a89e8c94260801ef3603f312a008c15bb072",
    "requirement": "R2",
    "result": "fail",
    "revision": "a12a5f17c1f2cc53ffcb08848fe4cd3f60723658",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "audit-probes-claimed"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T04:21:55+00:00",
  "relationships": {},
  "revision": "sha256:49980d8867878103d0cd3a7342b46365364559d16aa8beb35030114dc2d7818b",
  "subject": "audit-probes-claimed",
  "time": {
    "observed": "2026-10-18T04:21:55+00:00",
    "recorded": "2026-10-18T04:21:55+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_r2_audit_reports_unclaimed_probe_difference _______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-296/test_r2_audit_reports_unclaime0')

    def test_r2_audit_reports_unclaimed_probe_difference(tmp_path: Path):
        """R2: the audit reports a difference that no cited claim id accounts for."""
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
>       diffs = [d for d in payload["diffs"] if d.get("probe") == "value-print"]
E       KeyError: 'diffs'

tests/test_audit_probes.py:132: KeyError
=========================== short test summary info ============================
FAILED tests/test_audit_probes.py::test_r2_audit_reports_unclaimed_probe_difference
1 failed in 0.12s
