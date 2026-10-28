---
{
  "id": "rec-e69ef80b-1d8b-4a62-b353-3b3efb5c9aef",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7f25877d-2058-4e56-84df-4f27ce796323",
    "diff_sha256": "f4d0f674bd624548e84ab90f3e2bdb1978c8ff3997a5cca8c162be0f3dc1e70f",
    "duration_s": 3.005159,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_contents.py::test_r27_providers_json"
    ],
    "informed_by": [
      "rec-7f25877d-2058-4e56-84df-4f27ce796323"
    ],
    "method": "tdd",
    "output_sha256": "a86cef8ca89a2ee39888704934520fc9734306cd134260e7d6c0d0742b256425",
    "requirement": "R27",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T07:28:09+00:00",
  "relationships": {},
  "revision": "sha256:f0d7b77bd43086021eb23a144bd3a59c9b3abad12598d55229b23fa0c8791201",
  "subject": "declare-wheel-providers"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________________ test_r27_providers_json ____________________________

wheel_install = <test_wheel_contents._Install object at 0x747eb2450ac0>

    def test_r27_providers_json(wheel_install: _Install) -> None:
        """R27: `installer.matrix` loads `providers.json` from the installed `installer` package."""
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                _PROVIDERS_JSON,
                wheel_install.sites(),
                str(wheel_install.source.resolve()),
                str(REPO_ROOT.resolve()),
            ],
            capture_output=True,
            text=True,
        )
>       _assert_success(proc)

tests/test_wheel_contents.py:343:
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
FAILED tests/test_wheel_contents.py::test_r27_providers_json - AssertionError...
1 failed in 2.41s
