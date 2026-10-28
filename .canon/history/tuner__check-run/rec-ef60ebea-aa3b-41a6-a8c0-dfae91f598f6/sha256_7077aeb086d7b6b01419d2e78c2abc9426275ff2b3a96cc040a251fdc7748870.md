---
{
  "id": "rec-ef60ebea-aa3b-41a6-a8c0-dfae91f598f6",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-724d44d1-d272-46f3-9252-02d86f2bfa29",
    "diff_sha256": "b4da477fa2ab589fb729734ea8401fef55979e128f760ffb1e06fb763d6fabcc",
    "duration_s": 0.675573,
    "effort": "composer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_composer_schema.py::test_idea_bad_area"
    ],
    "informed_by": [
      "rec-724d44d1-d272-46f3-9252-02d86f2bfa29"
    ],
    "method": "tdd",
    "output_sha256": "45237891a4142277e435f90f5cfa8fe133fc8c6430094a4397e15d7291675031",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-27T23:48:02+00:00",
  "relationships": {},
  "revision": "sha256:7077aeb086d7b6b01419d2e78c2abc9426275ff2b3a96cc040a251fdc7748870",
  "subject": "composer-module-idea-bad-area"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________________ test_idea_bad_area ______________________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-107/test_idea_bad_area0')

    def test_idea_bad_area(tmp_path: Path):
>       root, env, _ = _init_store_with_composer(tmp_path)

tests/test_composer_schema.py:221:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-107/test_idea_bad_area0')

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
E        +  where 4 = CompletedProcess(args=['/usr/bin/python3', '-m', 'orchestra.canon', '--root', '/tmp/pytest-of-andrewyin/pytest-107/tes...y: \'/home/andrewyin/orchestra/.worktrees/composer-schema/orchestra/composer/schemas/composer.json\'"\n}\n', stderr='').returncode

tests/test_composer_schema.py:80: AssertionError
=========================== short test summary info ============================
FAILED tests/test_composer_schema.py::test_idea_bad_area - AssertionError: {
1 failed in 0.19s
