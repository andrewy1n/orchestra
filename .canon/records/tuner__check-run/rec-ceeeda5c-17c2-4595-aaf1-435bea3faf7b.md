---
{
  "id": "rec-ceeeda5c-17c2-4595-aaf1-435bea3faf7b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-9ef3e36f-3de3-40cd-b31e-81742dee49ef",
    "diff_sha256": "d51106eeb3cb0259a4059e5bf17ac38913b83c07d304104e11c7ac4aa18e4f18",
    "duration_s": 2.908951,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_contents.py::test_r8_uvicorn"
    ],
    "informed_by": [
      "rec-9ef3e36f-3de3-40cd-b31e-81742dee49ef"
    ],
    "method": "tdd",
    "output_sha256": "5915b4a0a9c91d4da1c40848c69fca23ef0bbc85cca9ad29f89aa8db990e02b7",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T07:28:05+00:00",
  "relationships": {},
  "revision": "sha256:17fd75ffcae66a6c90835d0131a9347067b603442919300af1ba37a749955ea6",
  "subject": "declare-wheel-uvicorn"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r8_uvicorn ________________________________

editable_install = <test_wheel_contents._Install object at 0x7e5bcf140610>

    def test_r8_uvicorn(editable_install: _Install) -> None:
        """R8: That install imports `uvicorn`."""
>       _assert_success(_run_install_import(editable_install, "uvicorn"))

tests/test_wheel_contents.py:325:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

proc = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...rce', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'uvicorn'\n")

    def _assert_success(proc: subprocess.CompletedProcess[str]) -> None:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
>       assert proc.returncode == 0, lines[-1] if lines else f"exit {proc.returncode}"
E       AssertionError: ModuleNotFoundError: No module named 'uvicorn'
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...rce', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'uvicorn'\n").returncode

tests/test_wheel_contents.py:268: AssertionError
=========================== short test summary info ============================
FAILED tests/test_wheel_contents.py::test_r8_uvicorn - AssertionError: Module...
1 failed in 2.34s
