---
{
  "id": "rec-734a65dc-b599-4d43-82c2-def27ed9cdcd",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-4ac56f49-8e3e-4d6f-9504-aacf0f8950e1",
    "diff_sha256": "73688fbf22e4871515deaace24c042bf4566f813a9af6da0ff940e60804171b8",
    "duration_s": 0.499326,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_attestation.py::test_ci_workflow_runs_verdict_and_attest"
    ],
    "informed_by": [
      "rec-4ac56f49-8e3e-4d6f-9504-aacf0f8950e1"
    ],
    "method": "tdd",
    "output_sha256": "23184114f5c41f7fb2ac256d9e36c675feb84f724b6186f32bbf14cf18370b34",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "ci-fixture-builder-pytest"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T06:02:11+00:00",
  "relationships": {},
  "revision": "sha256:8568a05963a7496dd81a75b9d5ed440e2ff781350adcda8afac08c3d7a09922e",
  "subject": "ci-fixture-builder-pytest",
  "time": {
    "observed": "2026-10-18T06:02:11+00:00",
    "recorded": "2026-10-18T06:02:11+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________ test_ci_workflow_runs_verdict_and_attest ___________________

    def test_ci_workflow_runs_verdict_and_attest() -> None:
        """R4: workflow must run an explicit fixture-build step and ship templates —
        not merely contain the strings verdict and attest."""
        workflows = REPO_ROOT / ".github" / "workflows"
        assert workflows.is_dir(), "expected .github/workflows"
        files = sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml"))
        assert files, "expected at least one workflow file"
        text = "\n".join(path.read_text() for path in files)
        assert "verdict" in text, "workflow must run aff verdict"
        assert "attest" in text, "workflow must invoke the attest emit path"
>       assert "build_verdict_repo" in text, (
            "workflow must invoke an explicit fixture builder (build_verdict_repo) "
            "before aff verdict"
        )
E       AssertionError: workflow must invoke an explicit fixture builder (build_verdict_repo) before aff verdict
E       assert 'build_verdict_repo' in '# Fixture CI: run aff verdict, emit a signed attestation, then verify it.\n#\n# Required secrets / allowlist (fixture...tion\n          path: |\n            verdict.json\n            attestation.json\n          if-no-files-found: ignore\n'

tests/test_attestation.py:207: AssertionError
=========================== short test summary info ============================
FAILED tests/test_attestation.py::test_ci_workflow_runs_verdict_and_attest - ...
1 failed in 0.04s
