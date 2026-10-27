---
{
  "id": "rec-e5aba151-3f80-4d42-abbd-314821a3fede",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e193d864-3ef9-414f-9067-c03c3968c92d",
    "duration_s": 3.050579,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_evidence_bind.py::test_r5_verdict_adds_observation_not_binding"
    ],
    "informed_by": [
      "rec-e193d864-3ef9-414f-9067-c03c3968c92d"
    ],
    "method": "tdd",
    "output_sha256": "b93dcb80b5b948ef6c157e463409d806734bafdc5450bc1f96baa7e7eeafe55e",
    "requirement": "R5",
    "result": "fail",
    "revision": "21bb6fa8337eab7e8d3a959863699c9672e1041e",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "bind-cli-verdict"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T09:44:53+00:00",
  "relationships": {},
  "revision": "sha256:f3cc71ad122945b25471e78d39d17095b25200193cb0dd68c6f6812d9c82219b",
  "subject": "bind-cli-verdict",
  "time": {
    "observed": "2026-10-18T09:44:53+00:00",
    "recorded": "2026-10-18T09:44:53+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_________________ test_r5_verdict_adds_observation_not_binding _________________

store = PosixPath('/tmp/se-workflow-test-u3u2xdvp')

    def test_r5_verdict_adds_observation_not_binding(store: Path) -> None:
        """R5: a passing verdict records one observation and no evidence-binding."""
        base, head = _seed_verdict_subject(store)
        before_obs = _list_evidence_observations(store)
        before_bind = _list_typed(store, BINDING_TYPE)

        proc = _verdict(store, base, head)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _payload(proc)["result"] == "pass"

        after_obs = _list_evidence_observations(store)
        assert len(after_obs) == len(before_obs) + 1, (
            f"expected one new {OBS_TYPE} after verdict; "
            f"before={len(before_obs)} after={len(after_obs)}"
        )
>       assert before_bind.returncode == 0, before_bind.stdout + before_bind.stderr
E       AssertionError: {
E           "error": "unknown_type",
E           "type": "project:evidence-binding"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/usr/bin/python3', '/home/andrewyin/adaptive-artifacts/tools/artifacts.py', '--root', '/tmp/se...', 'json'], returncode=4, stdout='{\n  "error": "unknown_type",\n  "type": "project:evidence-binding"\n}\n', stderr='').returncode

tests/test_evidence_bind.py:401: AssertionError
=========================== short test summary info ============================
FAILED tests/test_evidence_bind.py::test_r5_verdict_adds_observation_not_binding
1 failed in 2.56s
