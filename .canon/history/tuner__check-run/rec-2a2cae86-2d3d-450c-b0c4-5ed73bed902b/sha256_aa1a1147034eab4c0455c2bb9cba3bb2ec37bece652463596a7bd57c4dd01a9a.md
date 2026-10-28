---
{
  "id": "rec-2a2cae86-2d3d-450c-b0c4-5ed73bed902b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-1d2943cc-e146-488c-9103-8b6903bce2ae",
    "diff_sha256": "1ea130178643a1cd4f58de06bcf9aa067c0eb421470a04f12debdde1581f42fa",
    "duration_s": 3.028353,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_contents.py::test_r4_installer_adapters"
    ],
    "informed_by": [
      "rec-1d2943cc-e146-488c-9103-8b6903bce2ae"
    ],
    "method": "tdd",
    "output_sha256": "e17c808cbfd697cd559a36caab5b8b58075858436f70d3f094821e1333df44fd",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T07:27:50+00:00",
  "relationships": {},
  "revision": "sha256:aa1a1147034eab4c0455c2bb9cba3bb2ec37bece652463596a7bd57c4dd01a9a",
  "subject": "declare-wheel-adapters"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________________ test_r4_installer_adapters __________________________

editable_install = <test_wheel_contents._Install object at 0x787dd7a90a00>

    def test_r4_installer_adapters(editable_install: _Install) -> None:
        """R4: An editable install imports `installer.adapters` when the repository root is absent from `sys.path`."""
>       _assert_success(_run_install_import(editable_install, "installer.adapters"))

tests/test_wheel_contents.py:305:
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
FAILED tests/test_wheel_contents.py::test_r4_installer_adapters - AssertionEr...
1 failed in 2.40s
