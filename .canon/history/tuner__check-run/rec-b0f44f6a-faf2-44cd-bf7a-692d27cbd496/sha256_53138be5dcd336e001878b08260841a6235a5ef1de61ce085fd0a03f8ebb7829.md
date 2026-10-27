---
{
  "id": "rec-b0f44f6a-faf2-44cd-bf7a-692d27cbd496",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7",
    "duration_s": 0.591185,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_orchestra_callers.py::test_r3"
    ],
    "informed_by": [
      "rec-2dfbc2f6-8e1a-430b-87d3-6e6b44627ca7"
    ],
    "method": "tdd",
    "output_sha256": "d07f9bb53b66075e9b3fd9b18555173e81621675dfc20f2f0aeed97a4140c6bf",
    "requirement": "R3",
    "result": "fail",
    "revision": "cdcb9861c1b7f82caf097b00472d16f902d8d5b9",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "replace-resolvers-aa"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T10:43:58+00:00",
  "relationships": {},
  "revision": "sha256:53138be5dcd336e001878b08260841a6235a5ef1de61ce085fd0a03f8ebb7829",
  "subject": "replace-resolvers-aa",
  "time": {
    "observed": "2026-10-21T10:43:58+00:00",
    "recorded": "2026-10-21T10:43:58+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________________________ test_r3 ____________________________________

    def test_r3():
        """R3: orchestra/aa_resolve.py is not in the tree."""
        path = ROOT / "orchestra" / "aa_resolve.py"
>       assert not path.exists(), f"{path.relative_to(ROOT)} is still in the tree"
E       AssertionError: orchestra/aa_resolve.py is still in the tree
E       assert not True
E        +  where True = exists()
E        +    where exists = PosixPath('/home/andrewyin/orchestra/.worktrees/orchestra-callers/orchestra/aa_resolve.py').exists

tests/test_orchestra_callers.py:405: AssertionError
=========================== short test summary info ============================
FAILED tests/test_orchestra_callers.py::test_r3 - AssertionError: orchestra/a...
1 failed in 0.05s
