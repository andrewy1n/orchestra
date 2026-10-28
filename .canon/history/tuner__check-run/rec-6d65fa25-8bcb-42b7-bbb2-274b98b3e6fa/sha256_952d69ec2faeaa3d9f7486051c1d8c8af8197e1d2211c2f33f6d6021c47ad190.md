---
{
  "id": "rec-6d65fa25-8bcb-42b7-bbb2-274b98b3e6fa",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-f1a8a4bc-b660-4a70-a32c-adb4a3b3b6a1",
    "diff_sha256": "b4da477fa2ab589fb729734ea8401fef55979e128f760ffb1e06fb763d6fabcc",
    "duration_s": 1.951429,
    "effort": "composer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_composer_schema.py::test_installed_prefix_entry_point"
    ],
    "informed_by": [
      "rec-f1a8a4bc-b660-4a70-a32c-adb4a3b3b6a1"
    ],
    "method": "tdd",
    "output_sha256": "71dc46e18d8078542cb72e272aa707ac3c9a9c993fa7a42a6c2cb288e1f0c3dd",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-27T23:48:21+00:00",
  "relationships": {},
  "revision": "sha256:952d69ec2faeaa3d9f7486051c1d8c8af8197e1d2211c2f33f6d6021c47ad190",
  "subject": "verify-composer-schema-entry-point"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________ test_installed_prefix_entry_point _______________________

installed_prefix = {'env': {'AI_AGENT': 'claude-code_2-1-308_agent', 'BUN_INSTALL': '/home/andrewyin/.bun', 'CLAUDECODE': '1', 'CLAUDE_CODE_CHILD_SESSION': '1', ...}, 'error': None, 'prefix': PosixPath('/tmp/pytest-of-andrewyin/pytest-113/composer-prefix0')}
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-113/test_installed_prefix_entry_po0')

    def test_installed_prefix_entry_point(installed_prefix, tmp_path: Path):
        assert installed_prefix["error"] is None, installed_prefix["error"]
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import importlib.metadata as md, json\n"
                    "eps = md.entry_points()\n"
                    "group = eps.select(group='canon.schemas') if hasattr(eps, 'select') else eps.get('canon.schemas', [])\n"
                    "print(json.dumps({ep.name: ep.value for ep in group}, sort_keys=True))\n"
                ),
            ],
            cwd=str(elsewhere),
            env=installed_prefix["env"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, _output(proc)
        mapping = json.loads(proc.stdout or "{}")
>       assert mapping.get("composer") == "orchestra.composer.schemas"
E       AssertionError: assert None == 'orchestra.composer.schemas'
E        +  where None = <built-in method get of dict object at 0x7c41c609c8c0>('composer')
E        +    where <built-in method get of dict object at 0x7c41c609c8c0> = {'conductor': 'orchestra.conductor.schemas', 'score': 'orchestra.score.schemas', 'tuner': 'orchestra.tuner.schemas'}.get

tests/test_composer_schema.py:390: AssertionError
=========================== short test summary info ============================
FAILED tests/test_composer_schema.py::test_installed_prefix_entry_point - Ass...
1 failed in 1.45s
