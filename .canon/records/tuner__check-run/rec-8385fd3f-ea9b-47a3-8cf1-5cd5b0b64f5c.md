---
{
  "id": "rec-8385fd3f-ea9b-47a3-8cf1-5cd5b0b64f5c",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-fd0c2dd4-ef2d-452f-94dd-e9ba4aa26ffa",
    "diff_sha256": "fd9d7734ac9e10abb19025f20ecd0ffc9dfadc3930054f8bc9274db2bef7453d",
    "duration_s": 0.4976,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_effort_brief.py::test_r4_brief_with_four_sections_and_valid_effort_is_created"
    ],
    "informed_by": [
      "rec-fd0c2dd4-ef2d-452f-94dd-e9ba4aa26ffa"
    ],
    "method": "tdd",
    "output_sha256": "6592be42a3ec30a9e86dbd0a05baca0a8c754a6f97e69e95e926008cbbeb9fdc",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T17:07:36+00:00",
  "relationships": {},
  "revision": "sha256:787901a0bb0254d76b08f80dae34ed300adc4f5051c4f127b4d5e74ffdf97217",
  "subject": "brief-schema-r4"
}
---

F                                                                                                                                                                                                                                                  [100%]
======================================================================================================================== FAILURES ========================================================================================================================
______________________________________________________________________________________________ test_r4_brief_with_four_sections_and_valid_effort_is_created ______________________________________________________________________________________________

current_store = PosixPath('/tmp/se-workflow-test-36hboijj')

    def test_r4_brief_with_four_sections_and_valid_effort_is_created(current_store):
        result = _create_brief(current_store, "full", _body())
>       assert result.returncode == 0, _output(result)
E       AssertionError: {
E           "error": "unknown_type",
E           "message": "unknown record type: 'score:brief'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/effort-brief/.venv/bin/python', '-m', 'orchestra.canon', ...urncode=4, stdout='{\n  "error": "unknown_type",\n  "message": "unknown record type: \'score:brief\'"\n}\n', stderr='').returncode

tests/test_effort_brief.py:116: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_effort_brief.py::test_r4_brief_with_four_sections_and_valid_effort_is_created - AssertionError: {
1 failed, 10 deselected in 0.27s
