---
{
  "id": "rec-4e4aebb5-e6e3-4941-80b3-e98beb6f8f8e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-54233748-dfc1-4b0a-bc6f-8d36193677a8",
    "diff_sha256": "e0972315a70ebba984c30db90f648e2d9914592687c6b230a078d54865c77e70",
    "duration_s": 1.9342,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_analyze_cli.py::test_r5_default_stage_is_plan",
      "tests/test_analyze_cli.py::test_r5_plan_stage_reports_no_check_run_finding",
      "tests/test_analyze_cli.py::test_r5_explicit_plan_stage_matches_the_default"
    ],
    "informed_by": [
      "rec-54233748-dfc1-4b0a-bc6f-8d36193677a8"
    ],
    "method": "tdd",
    "output_sha256": "7ae7a68b05d36dbfc797ba52e44e000f27bcffb2fa8ae7f6542ad8695d88d92c",
    "requirement": "R5",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T08:12:03+00:00",
  "relationships": {},
  "revision": "sha256:d4d186f677baf4fe9a9e108877c87e14c1135fcbfe0e795cc9fe5d4bd4b87b6a",
  "subject": "analyze-cli-r5"
}
---

====================================================================================
_____________________________________________________________________________________________________________ test_r5_default_stage_is_plan ______________________________________________________________________________________________________________

store = PosixPath('/tmp/se-workflow-test-72rhidr2'), cli = <function cli.<locals>._run at 0x70c4feaa9ee0>
resolved_contract = {'records': [{'id': 'composer:area', 'name': 'area', 'purpose': 'A named, long-lived product area', 'fields': {'title'...nment': {'ref': 'conductor:assignment'}, 'result': {'type': 'string'}, 'verdict': {'type': 'string'}, ...}, ...}, ...]}

    def test_r5_default_stage_is_plan(store, cli, resolved_contract):
        seed_phase(cli, resolved_contract)
>       _, report = analyze_json(store)
                    ^^^^^^^^^^^^^^^^^^^

tests/test_analyze_cli.py:79:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-72rhidr2'), slug = 'analyze-phase', args = ()

    def analyze_json(store: Path, *args: str, slug: str = SLUG) -> tuple[int, dict]:
        result = run_analyze(store, "--json", *args, slug=slug)
>       assert result.stdout.strip(), result.stdout + result.stderr
E       AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
E         orchestra: error: argument command: invalid choice: 'analyze' (choose from handoff, view, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)
E
E       assert ''
E        +  where '' = <built-in method strip of str object at 0x70c501ef0f38>()
E        +    where <built-in method strip of str object at 0x70c501ef0f38> = ''.strip
E        +      where '' = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/spec-analyze/.venv/bin/python', '-m', 'orchestra.cli', 'a...iew, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)\n").stdout

tests/test_analyze.py:48: AssertionError
____________________________________________________________________________________________________ test_r5_plan_stage_reports_no_check_run_finding _____________________________________________________________________________________________________

store = PosixPath('/tmp/se-workflow-test-u2rd40tu'), cli = <function cli.<locals>._run at 0x70c4feadd8a0>
resolved_contract = {'records': [{'id': 'composer:area', 'name': 'area', 'purpose': 'A named, long-lived product area', 'fields': {'title'...nment': {'ref': 'conductor:assignment'}, 'result': {'type': 'string'}, 'verdict': {'type': 'string'}, ...}, ...}, ...]}

    def test_r5_plan_stage_reports_no_check_run_finding(store, cli, resolved_contract):
        seed_phase(cli, resolved_contract)
>       code, report = analyze_json(store)
                       ^^^^^^^^^^^^^^^^^^^

tests/test_analyze_cli.py:85:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-u2rd40tu'), slug = 'analyze-phase', args = ()

    def analyze_json(store: Path, *args: str, slug: str = SLUG) -> tuple[int, dict]:
        result = run_analyze(store, "--json", *args, slug=slug)
>       assert result.stdout.strip(), result.stdout + result.stderr
E       AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
E         orchestra: error: argument command: invalid choice: 'analyze' (choose from handoff, view, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)
E
E       assert ''
E        +  where '' = <built-in method strip of str object at 0x70c501ef0f38>()
E        +    where <built-in method strip of str object at 0x70c501ef0f38> = ''.strip
E        +      where '' = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/spec-analyze/.venv/bin/python', '-m', 'orchestra.cli', 'a...iew, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)\n").stdout

tests/test_analyze.py:48: AssertionError
____________________________________________________________________________________________________ test_r5_explicit_plan_stage_matches_the_default _____________________________________________________________________________________________________

store = PosixPath('/tmp/se-workflow-test-dt2gjbpq'), cli = <function cli.<locals>._run at 0x70c4feaddc60>
resolved_contract = {'records': [{'id': 'composer:area', 'name': 'area', 'purpose': 'A named, long-lived product area', 'fields': {'title'...nment': {'ref': 'conductor:assignment'}, 'result': {'type': 'string'}, 'verdict': {'type': 'string'}, ...}, ...}, ...]}

    def test_r5_explicit_plan_stage_matches_the_default(store, cli, resolved_contract):
        seed_phase(cli, resolved_contract, item_ids=("R1",))
>       default = analyze_json(store)
                  ^^^^^^^^^^^^^^^^^^^

tests/test_analyze_cli.py:93:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-dt2gjbpq'), slug = 'analyze-phase', args = ()

    def analyze_json(store: Path, *args: str, slug: str = SLUG) -> tuple[int, dict]:
        result = run_analyze(store, "--json", *args, slug=slug)
>       assert result.stdout.strip(), result.stdout + result.stderr
E       AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
E         orchestra: error: argument command: invalid choice: 'analyze' (choose from handoff, view, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)
E
E       assert ''
E        +  where '' = <built-in method strip of str object at 0x70c501ef0f38>()
E        +    where <built-in method strip of str object at 0x70c501ef0f38> = ''.strip
E        +      where '' = CompletedProcess(args=['/home/andrewyin/orchestra/.worktrees/spec-analyze/.venv/bin/python', '-m', 'orchestra.cli', 'a...iew, brief, hook-start, hook-stop, verify, check, close-batch, install, sessions, review-brief, suite, store, idea)\n").stdout

tests/test_analyze.py:48: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_analyze_cli.py::test_r5_default_stage_is_plan - AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
FAILED tests/test_analyze_cli.py::test_r5_plan_stage_reports_no_check_run_finding - AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
FAILED tests/test_analyze_cli.py::test_r5_explicit_plan_stage_matches_the_default - AssertionError: usage: orchestra [-h] {handoff,view,brief,hook-start,hook-stop,verify,check,close-batch,install,sessions,review-brief,suite,store,idea} ...
3 failed, 11 deselected in 1.71s
