---
{
  "id": "rec-3bfc1262-c7f7-4f31-ace6-a8936cfaaa2c",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "evidence-interface-suite",
    "duration_s": 42096.244156,
    "effort": "evidence-layer",
    "evidence_kind": "integration",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_claim_authoring.py::test_r2_standalone_add_freeze_verdict_passes"
    ],
    "method": "check",
    "output_sha256": "488d4a9e365412b125f2701c4f6d48738ba8f0c12ca74b8388f43f43778f9e92",
    "result": "fail",
    "revision": "a655bf41071f6783be3049a8107ac8e28c54ee55",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "evidence-interface-suite"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T09:18:50+00:00",
  "relationships": {},
  "revision": "sha256:f0532cd150129517fc9f2473e64282e69c8e46b7a0c78689f480af4335240f47",
  "subject": "evidence-interface-suite",
  "time": {
    "observed": "2026-10-18T09:18:50+00:00",
    "recorded": "2026-10-18T09:18:50+00:00"
  }
}
---

bringing up nodes...
bringing up nodes...

.....................F.................................................. [ 63%]
.........................................                                [100%]
=================================== FAILURES ===================================
_________________ test_r2_standalone_add_freeze_verdict_passes _________________
[gw1] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmpXDMUcP/bin/python

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-446/popen-gw1/test_r2_standalone_add_freeze_0')

    def test_r2_standalone_add_freeze_verdict_passes(tmp_path):
        """R2: claim add + freeze + verdict passes end to end with no orchestra on PATH."""
        root = tmp_path / "repo"
        _init(root)
        (root / "pytest.ini").write_text("[pytest]\n")
        (root / "tests").mkdir()
        (root / ORACLE_REL).write_bytes(ORACLE)
        (root / "app.py").write_bytes(APP_RED)
        (root / ".affidavit").mkdir()
        (root / ".affidavit" / "allowed_signers").write_bytes(ALLOW)

        added = _aff(
            "claim", "add", "--cwd", str(root),
            "--id", "claim-widget", "--text", "value is one", "--test", NODE,
        )
        assert added.returncode == 0, added.stderr
        frozen = _aff("freeze", "--cwd", str(root))
        assert frozen.returncode == 0, frozen.stderr
        base = _commit(root, "red")

        (root / "app.py").write_bytes(APP_GREEN)
        head = _commit(root, "green")

        proc = _aff(
            "verdict", "--cwd", str(root), "--base", base, "--at", head, "claim-widget"
        )
>       assert proc.returncode == 0, proc.stdout + proc.stderr
E       AssertionError: Traceback (most recent call last):
E           File "/home/andrewyin/affidavit--evidence-interface/bin/aff", line 15, in <module>
E             sys.exit(main(sys.argv[1:]))
E                      ~~~~^^^^^^^^^^^^^^
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/cli.py", line 228, in main
E             payload = run_verdict(
E                 work, args.at, args.base, args.claim_ids, provenance=args.provenance
E             )
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/verdict.py", line 131, in run_verdict
E             _judge_pending(
E             ~~~~~~~~~~~~~~^
E                 root,
E                 ^^^^^
E             ...<5 lines>...
E                 verdicts,
E                 ^^^^^^^^^
E             )
E             ^
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/verdict.py", line 225, in _judge_pending
E             base_first = _outcomes(_worktree(base_tree), base_ids, base_runner)
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/verdict.py", line 263, in _outcomes
E             return run_tests(worktree, test_ids, runner)
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/runner.py", line 38, in run_tests
E             grouped = _read_report(report)
E           File "/home/andrewyin/affidavit--evidence-interface/affidavit/runner.py", line 56, in _read_report
E             for case in ET.parse(path).getroot().iter():
E                         ~~~~~~~~^^^^^^
E           File "/home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/xml/etree/ElementTree.py", line 1204, in parse
E             tree.parse(source, parser)
E             ~~~~~~~~~~^^^^^^^^^^^^^^^^
E           File "/home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/xml/etree/ElementTree.py", line 569, in parse
E             self._root = parser._parse_whole(source)
E                          ~~~~~~~~~~~~~~~~~~~^^^^^^^^
E         xml.etree.ElementTree.ParseError: no element found: line 1, column 0
E
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/andrewyin/.cache/uv/builds-v0/.tmpXDMUcP/bin/python', '/home/andrewyin/affidavit--eviden...n                 ~~~~~~~~~~~~~~~~~~~^^^^^^^^\nxml.etree.ElementTree.ParseError: no element found: line 1, column 0\n').returncode

tests/test_claim_authoring.py:286: AssertionError
=========================== short test summary info ============================
FAILED tests/test_claim_authoring.py::test_r2_standalone_add_freeze_verdict_passes
1 failed, 112 passed in 29.89s


## Failing node IDs

- tests/test_claim_authoring.py::test_r2_standalone_add_freeze_verdict_passes
