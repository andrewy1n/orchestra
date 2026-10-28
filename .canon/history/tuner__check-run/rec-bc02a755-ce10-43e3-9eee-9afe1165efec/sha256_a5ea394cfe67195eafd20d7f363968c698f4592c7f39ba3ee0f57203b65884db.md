---
{
  "id": "rec-bc02a755-ce10-43e3-9eee-9afe1165efec",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-80d520f2-e20f-492a-8193-678ca9d77ff0",
    "diff_sha256": "b4da477fa2ab589fb729734ea8401fef55979e128f760ffb1e06fb763d6fabcc",
    "duration_s": 0.676946,
    "effort": "composer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_composer_schema.py::test_idea_bad_phase"
    ],
    "informed_by": [
      "rec-80d520f2-e20f-492a-8193-678ca9d77ff0"
    ],
    "method": "tdd",
    "output_sha256": "07153b672a511307fdf43054499a56b9ed4f2760e92dea2f39de3d4c404e26d4",
    "requirement": "R11",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-27T23:48:07+00:00",
  "relationships": {},
  "revision": "sha256:a5ea394cfe67195eafd20d7f363968c698f4592c7f39ba3ee0f57203b65884db",
  "subject": "composer-module-idea-bad-phase"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_idea_bad_phase ______________________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-109/test_idea_bad_phase0')

    def test_idea_bad_phase(tmp_path: Path):
>       root, env, _ = _init_store_with_composer(tmp_path)

tests/test_composer_schema.py:283:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-109/test_idea_bad_phase0')

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
E        +  where 4 = CompletedProcess(args=['/usr/bin/python3', '-m', 'orchestra.canon', '--root', '/tmp/pytest-of-andrewyin/pytest-109/tes...y: \'/home/andrewyin/orchestra/.worktrees/composer-schema/orchestra/composer/schemas/composer.json\'"\n}\n', stderr='').returncode

tests/test_composer_schema.py:80: AssertionError
=========================== short test summary info ============================
FAILED tests/test_composer_schema.py::test_idea_bad_phase - AssertionError: {
1 failed in 0.15s
