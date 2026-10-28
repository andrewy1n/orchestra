---
{
  "id": "rec-98b5cdd8-dc22-4cdf-a217-93f819a9b8fb",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-672084da-9533-4625-b058-15d879e49500",
    "diff_sha256": "b4da477fa2ab589fb729734ea8401fef55979e128f760ffb1e06fb763d6fabcc",
    "duration_s": 0.880801,
    "effort": "composer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_composer_schema.py::test_area_needs_scope"
    ],
    "informed_by": [
      "rec-672084da-9533-4625-b058-15d879e49500"
    ],
    "method": "tdd",
    "output_sha256": "49da81dfb23517087c0fa77dc807401c77f96136070b42e6bfd8897395103c6c",
    "requirement": "R6",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-27T23:47:55+00:00",
  "relationships": {},
  "revision": "sha256:97ae0812a6b140bac974f27e7d44338716a2a3e20989af3141e5bc38310c5e6b",
  "subject": "composer-module-area-needs-scope"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________________________ test_area_needs_scope _____________________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-104/test_area_needs_scope0')

    def test_area_needs_scope(tmp_path: Path):
>       root, env, _ = _init_store_with_composer(tmp_path)

tests/test_composer_schema.py:167:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-104/test_area_needs_scope0')

    def _init_store_with_composer(tmp_path: Path) -> tuple[Path, dict[str, str], dict[str, object]]:
        root = _make_git_repo(tmp_path)
        env = _composer_env()
        init = _run_canon(root, env, "init", "--schemas", "score,conductor,tuner,composer")
>       assert init.returncode == 0, _output(init)
E       AssertionError: {
E           "error": "schema",
E           "message": "cannot read schema module '/home/andrewyin/orchestra/.worktrees/composer-schema/orchestra/composer/schemas/composer.json' from CANON_SCHEMA_PATH: [Errno 2] No such file or directory: '/home/andrewyin/orchestra/.worktrees/composer-schema/orchestra/composer/schemas/composer.json'"
E         }
E
E       assert 4 == 0
E        +  where 4 = CompletedProcess(args=['/usr/bin/python3', '-m', 'orchestra.canon', '--root', '/tmp/pytest-of-andrewyin/pytest-104/tes...y: \'/home/andrewyin/orchestra/.worktrees/composer-schema/orchestra/composer/schemas/composer.json\'"\n}\n', stderr='').returncode

tests/test_composer_schema.py:80: AssertionError
=========================== short test summary info ============================
FAILED tests/test_composer_schema.py::test_area_needs_scope - AssertionError: {
1 failed in 0.16s
