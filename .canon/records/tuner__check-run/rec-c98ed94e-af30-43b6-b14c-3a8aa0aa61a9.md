---
{
  "id": "rec-c98ed94e-af30-43b6-b14c-3a8aa0aa61a9",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-f3089e32-212c-4acb-b663-0e5056a96dc1",
    "diff_sha256": "80ff88695a341bae7da1261d31db56c45163235ecab9ff26afc14efb475b1ddc",
    "duration_s": 2.993328,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_contents.py::test_r1_dashboard"
    ],
    "informed_by": [
      "rec-f3089e32-212c-4acb-b663-0e5056a96dc1"
    ],
    "method": "tdd",
    "output_sha256": "97c9f3b6d70ba16ebbb1f13b16fbe18484ee57a970764f04cf695a87c37d7412",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T07:27:35+00:00",
  "relationships": {},
  "revision": "sha256:032de949f15468f9b5e31f6cc76b999cf1ebe658696ef901e1c761eafccecfe1",
  "subject": "declare-wheel"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________________ test_r1_dashboard _______________________________

editable_install = <test_wheel_contents._Install object at 0x7b31827fcee0>

    def test_r1_dashboard(editable_install: _Install) -> None:
        """R1: An editable install imports `dashboard` when the repository root is absent from `sys.path`."""
>       _assert_success(_run_install_import(editable_install, "dashboard"))

tests/test_wheel_contents.py:290:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

proc = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...e', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'dashboard'\n")

    def _assert_success(proc: subprocess.CompletedProcess[str]) -> None:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
>       assert proc.returncode == 0, lines[-1] if lines else f"exit {proc.returncode}"
E       AssertionError: ModuleNotFoundError: No module named 'dashboard'
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...e', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'dashboard'\n").returncode

tests/test_wheel_contents.py:268: AssertionError
=========================== short test summary info ============================
FAILED tests/test_wheel_contents.py::test_r1_dashboard - AssertionError: Modu...
1 failed in 2.40s
