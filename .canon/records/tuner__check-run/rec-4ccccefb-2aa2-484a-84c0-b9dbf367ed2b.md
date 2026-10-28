---
{
  "id": "rec-4ccccefb-2aa2-484a-84c0-b9dbf367ed2b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-9b9a3c1b-4dcb-4061-bad2-f86157c8c180",
    "diff_sha256": "a42428e763bfd811ca7002b44844745d319ff83d0bd357028cc9d0bc3a822108",
    "duration_s": 2.865023,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_contents.py::test_r3_installer"
    ],
    "informed_by": [
      "rec-9b9a3c1b-4dcb-4061-bad2-f86157c8c180"
    ],
    "method": "tdd",
    "output_sha256": "781de21bc5cb486daba53a7398f31f33240a9a7c68118d058b51f8b2d60f5f53",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T07:27:43+00:00",
  "relationships": {},
  "revision": "sha256:666e26a0149620362b9873ece37fc94d39179fc6a53b4d87eb48fb9db9e6ad6c",
  "subject": "declare-wheel-installer"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________________ test_r3_installer _______________________________

editable_install = <test_wheel_contents._Install object at 0x776675df0d60>

    def test_r3_installer(editable_install: _Install) -> None:
        """R3: An editable install imports `installer` when the repository root is absent from `sys.path`."""
>       _assert_success(_run_install_import(editable_install, "installer"))

tests/test_wheel_contents.py:300:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

proc = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...e', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'installer'\n")

    def _assert_success(proc: subprocess.CompletedProcess[str]) -> None:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
>       assert proc.returncode == 0, lines[-1] if lines else f"exit {proc.returncode}"
E       AssertionError: ModuleNotFoundError: No module named 'installer'
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/usr/bin/python3', '-I', '-c', '\nimport site\nimport sys\nfrom pathlib import Path\n\nsites, ...e', '/home/andrewyin/orchestra'], returncode=1, stdout='', stderr="ModuleNotFoundError: No module named 'installer'\n").returncode

tests/test_wheel_contents.py:268: AssertionError
=========================== short test summary info ============================
FAILED tests/test_wheel_contents.py::test_r3_installer - AssertionError: Modu...
1 failed in 2.28s
