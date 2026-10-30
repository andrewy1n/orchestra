---
{
  "id": "rec-c018daf5-6b1e-4dd5-ad07-a2038ff0a0ea",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-c41e320c-b880-4fc4-adfa-613b992f8b24",
    "diff_sha256": "289c08f983e7cc61c376da71754e02849e900c3fd388551e2809d39a1eca8327",
    "duration_s": 0.269267,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/dashboard/test_ui_structure.py::test_r1_ui_lives_in_dashboard_frontend_and_dashboard_web_is_gone"
    ],
    "informed_by": [
      "rec-c41e320c-b880-4fc4-adfa-613b992f8b24"
    ],
    "method": "tdd",
    "output_sha256": "6152c50a1c79a032a66c72fb7f090d064c8bc3f177178c20b4947bf60a9382a5",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T21:37:56+00:00",
  "relationships": {},
  "revision": "sha256:661ccc107fa882e5a0affbc26bb276aee1505d4a0852edec908a74c2995c8610",
  "subject": "move-frontend"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______ test_r1_ui_lives_in_dashboard_frontend_and_dashboard_web_is_gone _______

    def test_r1_ui_lives_in_dashboard_frontend_and_dashboard_web_is_gone():
>       assert (FRONTEND / "package.json").is_file(), "missing dashboard/frontend/package.json"
E       AssertionError: missing dashboard/frontend/package.json
E       assert False
E        +  where False = is_file()
E        +    where is_file = (PosixPath('/home/andrewyin/orchestra/dashboard/frontend') / 'package.json').is_file

tests/dashboard/test_ui_structure.py:54: AssertionError
=========================== short test summary info ============================
FAILED tests/dashboard/test_ui_structure.py::test_r1_ui_lives_in_dashboard_frontend_and_dashboard_web_is_gone
1 failed in 0.04s
