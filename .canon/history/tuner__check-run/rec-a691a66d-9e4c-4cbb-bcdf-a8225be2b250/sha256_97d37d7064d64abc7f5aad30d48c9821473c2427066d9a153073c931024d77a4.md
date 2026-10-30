---
{
  "id": "rec-a691a66d-9e4c-4cbb-bcdf-a8225be2b250",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-31879332-dcb5-4ad6-854e-6d275f78718b",
    "diff_sha256": "11189c6454f38d9119f0fc7d0fbcc597da571fb7f6006bda550575437baddbf2",
    "duration_s": 0.259809,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/dashboard/test_data_layer.py::test_r1_only_store_py_calls_project_list_or_get"
    ],
    "informed_by": [
      "rec-31879332-dcb5-4ad6-854e-6d275f78718b"
    ],
    "method": "tdd",
    "output_sha256": "efee9a9c974c91ab8b4bcac7883d3c56d875ae9af6867b5f022297eeb234e76c",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T20:41:45+00:00",
  "relationships": {},
  "revision": "sha256:97d37d7064d64abc7f5aad30d48c9821473c2427066d9a153073c931024d77a4",
  "subject": "store-module"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_r1_only_store_py_calls_project_list_or_get ________________

    def test_r1_only_store_py_calls_project_list_or_get():
        store = BACKEND / "store.py"
>       assert store.is_file(), "missing dashboard/backend/store.py"
E       AssertionError: missing dashboard/backend/store.py
E       assert False
E        +  where False = is_file()
E        +    where is_file = PosixPath('/home/andrewyin/orchestra/dashboard/backend/store.py').is_file

tests/dashboard/test_data_layer.py:70: AssertionError
=========================== short test summary info ============================
FAILED tests/dashboard/test_data_layer.py::test_r1_only_store_py_calls_project_list_or_get
1 failed in 0.04s
