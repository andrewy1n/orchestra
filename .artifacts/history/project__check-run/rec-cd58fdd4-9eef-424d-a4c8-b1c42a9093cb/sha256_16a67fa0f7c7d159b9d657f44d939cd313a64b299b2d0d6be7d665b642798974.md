---
{
  "base_kind": "event",
  "id": "rec-cd58fdd4-9eef-424d-a4c8-b1c42a9093cb",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-3c86fb99-228d-40b6-99f7-5d48aa05de37",
    "diff_sha256": "00b901c017d0ed950de6e4dc91eb88d641bda17af8122043de1d38d3ba21f877",
    "duration_s": 0.581612,
    "effort": "workflow-loop",
    "exit_code": 1,
    "method": "tdd",
    "output_sha256": "73f5f54cd2ec9a1873eae5ea32c645f05fab6443624ae69607c44f81e056e682",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "close-batch-store-verify-missing"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-16T09:41:59+00:00",
  "relationships": {
    "informed_by": [
      "rec-3c86fb99-228d-40b6-99f7-5d48aa05de37",
      "rec-2da27c78-39a7-46cb-9580-6d3532c70b7d"
    ]
  },
  "revision": "sha256:16a67fa0f7c7d159b9d657f44d939cd313a64b299b2d0d6be7d665b642798974",
  "subject": "close-batch-store-verify-missing",
  "time": {
    "observed": "2026-10-16T09:41:59+00:00",
    "recorded": "2026-10-16T09:41:59+00:00"
  }
}
---

FF                                                                       [100%]
=================================== FAILURES ===================================
__________________ test_missing_check_run_id_is_request_error __________________

    def test_missing_check_run_id_is_request_error():
        request = _request(
            criteria=[
                {
                    "criterion_id": "rec-ac1",
                    "method": "tdd",
                    "result": "pass",
                }
            ]
        )
>       with pytest.raises(close_batch.CloseRequestError, match="check_run_id"):
E       AttributeError: module 'affidavit.close_batch' has no attribute 'CloseRequestError'

tests/test_close_batch.py:957: AttributeError
________ test_missing_result_is_request_error_not_result_optional_pass _________

    def test_missing_result_is_request_error_not_result_optional_pass():
        request = _request(
            criteria=[
                {
                    "criterion_id": "rec-ac1",
                    "method": "check",
                    "check_run_id": "rec-runner-cr",
                }
            ]
        )
>       with pytest.raises(close_batch.CloseRequestError, match="result"):
E       AttributeError: module 'affidavit.close_batch' has no attribute 'CloseRequestError'

tests/test_close_batch.py:971: AttributeError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_missing_check_run_id_is_request_error
FAILED tests/test_close_batch.py::test_missing_result_is_request_error_not_result_optional_pass
2 failed, 43 deselected in 0.06s
