---
{
  "id": "rec-ca8b2ff4-bfb6-43dc-a8e0-fd1688204c2f",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-467fa744-56e8-4f6e-9766-10f472bec388",
    "duration_s": 0.737929,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Problem]",
      "tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Users]",
      "tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Success",
      "tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Non-goals]"
    ],
    "informed_by": [
      "rec-467fa744-56e8-4f6e-9766-10f472bec388"
    ],
    "method": "tdd",
    "output_sha256": "3a590b522866333d5f515c4aac00f94e90a7044b30f04d722610dfa65b876ef0",
    "requirement": "R3",
    "result": "fail",
    "revision": "81eadd1bdcd9342782e4672d25be9bc425693a43",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T17:14:38+00:00",
  "relationships": {},
  "revision": "sha256:d4b734e110d35cf5e30ff0f70a8fa5e14ef46e7ee8401ff37b6cbe4b19216c95",
  "subject": "brief-schema-r3"
}
---

FFFF                                                                                                                                                                                                                                               [100%]
======================================================================================================================== FAILURES ========================================================================================================================
_________________________________________________________________________________________________ test_r3_missing_section_is_rejected_and_named[Problem] _________________________________________________________________________________________________

current_store = PosixPath('/tmp/se-workflow-test-5d7fo7ek'), missing = 'Problem'

    @pytest.mark.parametrize("missing", SECTIONS)
    def test_r3_missing_section_is_rejected_and_named(current_store, missing):
        accepted = _create_brief(current_store, f"control-{missing.lower().replace(' ', '-')}", _body())
>       assert accepted.returncode == 0, _output(accepted)
E       AssertionError: {
E           "error": "unknown_type",
E           "message": "unknown record type: 'score:brief'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/effort-brief/.venv/bin/python', '-m', 'orchestra.canon', ...urncode=4, stdout='{\n  "error": "unknown_type",\n  "message": "unknown record type: \'score:brief\'"\n}\n', stderr='').returncode

tests/test_effort_brief.py:107: AssertionError
__________________________________________________________________________________________________ test_r3_missing_section_is_rejected_and_named[Users] __________________________________________________________________________________________________

current_store = PosixPath('/tmp/se-workflow-test-5d7fo7ek'), missing = 'Users'

    @pytest.mark.parametrize("missing", SECTIONS)
    def test_r3_missing_section_is_rejected_and_named(current_store, missing):
        accepted = _create_brief(current_store, f"control-{missing.lower().replace(' ', '-')}", _body())
>       assert accepted.returncode == 0, _output(accepted)
E       AssertionError: {
E           "error": "unknown_type",
E           "message": "unknown record type: 'score:brief'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/effort-brief/.venv/bin/python', '-m', 'orchestra.canon', ...urncode=4, stdout='{\n  "error": "unknown_type",\n  "message": "unknown record type: \'score:brief\'"\n}\n', stderr='').returncode

tests/test_effort_brief.py:107: AssertionError
_____________________________________________________________________________________________ test_r3_missing_section_is_rejected_and_named[Success measure] _____________________________________________________________________________________________

current_store = PosixPath('/tmp/se-workflow-test-5d7fo7ek'), missing = 'Success measure'

    @pytest.mark.parametrize("missing", SECTIONS)
    def test_r3_missing_section_is_rejected_and_named(current_store, missing):
        accepted = _create_brief(current_store, f"control-{missing.lower().replace(' ', '-')}", _body())
>       assert accepted.returncode == 0, _output(accepted)
E       AssertionError: {
E           "error": "unknown_type",
E           "message": "unknown record type: 'score:brief'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/effort-brief/.venv/bin/python', '-m', 'orchestra.canon', ...urncode=4, stdout='{\n  "error": "unknown_type",\n  "message": "unknown record type: \'score:brief\'"\n}\n', stderr='').returncode

tests/test_effort_brief.py:107: AssertionError
________________________________________________________________________________________________ test_r3_missing_section_is_rejected_and_named[Non-goals] ________________________________________________________________________________________________

current_store = PosixPath('/tmp/se-workflow-test-5d7fo7ek'), missing = 'Non-goals'

    @pytest.mark.parametrize("missing", SECTIONS)
    def test_r3_missing_section_is_rejected_and_named(current_store, missing):
        accepted = _create_brief(current_store, f"control-{missing.lower().replace(' ', '-')}", _body())
>       assert accepted.returncode == 0, _output(accepted)
E       AssertionError: {
E           "error": "unknown_type",
E           "message": "unknown record type: 'score:brief'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/effort-brief/.venv/bin/python', '-m', 'orchestra.canon', ...urncode=4, stdout='{\n  "error": "unknown_type",\n  "message": "unknown record type: \'score:brief\'"\n}\n', stderr='').returncode

tests/test_effort_brief.py:107: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Problem] - AssertionError: {
FAILED tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Users] - AssertionError: {
FAILED tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Success measure] - AssertionError: {
FAILED tests/test_effort_brief.py::test_r3_missing_section_is_rejected_and_named[Non-goals] - AssertionError: {
4 failed, 7 deselected in 0.48s
