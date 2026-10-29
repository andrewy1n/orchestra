---
{
  "id": "rec-e7723d28-d65c-446b-8cd7-d3eabd7a8fb0",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-419a88a3-d91d-487d-8a37-0bb5b870714b",
    "diff_sha256": "680e7f58757251c7018fc4f8ceeb8a0ead2c1ce523a8557943d72686d21b187e",
    "duration_s": 0.272034,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_gate.py::test_r8_agents_md_has_a_ts_svelte_section"
    ],
    "informed_by": [
      "rec-419a88a3-d91d-487d-8a37-0bb5b870714b"
    ],
    "method": "tdd",
    "output_sha256": "218e3872ca8882cba97764bbd846ac57940bf6a1d99bdd9ce65aed5279403925",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T18:53:24+00:00",
  "relationships": {},
  "revision": "sha256:25e13590b89296c499e82221361b6821b25c7d6faa8ba5c231de3ca30244ce11",
  "subject": "agents-ts-section"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_r8_agents_md_has_a_ts_svelte_section ___________________

    def test_r8_agents_md_has_a_ts_svelte_section():
>       assert _ts_svelte_section() is not None, (
            "AGENTS.md has no TypeScript and Svelte heading"
        )
E       AssertionError: AGENTS.md has no TypeScript and Svelte heading
E       assert None is not None
E        +  where None = _ts_svelte_section()

tests/test_web_gate.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_gate.py::test_r8_agents_md_has_a_ts_svelte_section - As...
1 failed in 0.04s
