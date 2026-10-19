---
{
  "base_kind": "event",
  "id": "rec-c6fdbea3-524c-4c2c-a3e8-5ac7b6a729f5",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b97cbd55-140b-4868-8652-f4dda7f99ae8",
    "diff_sha256": "b1d411a3b1f8d7207a47f57915c3c7751f53d016a96f1f803a0237e9357964f2",
    "duration_s": 0.63605,
    "effort": "workflow-loop",
    "exit_code": 1,
    "method": "tdd",
    "output_sha256": "9830198318f90a359a7f00e69656b60df4b2e68ea0d88f5468ed263aaa90d0bf",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "close-batch-store-verify-revision"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-16T09:42:23+00:00",
  "relationships": {
    "informed_by": [
      "rec-b97cbd55-140b-4868-8652-f4dda7f99ae8",
      "rec-2da27c78-39a7-46cb-9580-6d3532c70b7d"
    ]
  },
  "revision": "sha256:b07f61c7d0ba33ef474b33ea6feff0a516b89b298e87f5fa418ed204567949f5",
  "subject": "close-batch-store-verify-revision",
  "time": {
    "observed": "2026-10-16T09:42:23+00:00",
    "recorded": "2026-10-16T09:42:23+00:00"
  }
}
---

FF                                                                       [100%]
=================================== FAILURES ===================================
________________ test_tdd_revision_without_red_is_request_error ________________

    def test_tdd_revision_without_red_is_request_error():
        request = _request(
            criteria=[
                {
                    "criterion_id": "rec-ac1",
                    "method": "tdd",
                    "check_run_id": "rec-runner-cr",
                    "result": "pass",
                    "revision": "abc123",
                }
            ]
        )
        with pytest.raises(close_batch.CloseRequestError, match="revision"):
>           _build(request)

tests/test_close_batch.py:939:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-cr', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'result': 'pass', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None, load_check_run = None, kwargs = {}
loader = <function _matching_loader.<locals>.load at 0x705117c75900>

    def _build(request: dict, *, cwd: Path | None = None, load_check_run=None, **kwargs):
        """build_batch with a matching store loader unless one is supplied."""
        loader = load_check_run
        if loader is None and request.get("transition") == "done":
            loader = _matching_loader(request)
>       return close_batch.build_batch(
            request, cwd=cwd, load_check_run=loader, **kwargs
        )
E       TypeError: build_batch() got an unexpected keyword argument 'load_check_run'

tests/test_close_batch.py:115: TypeError
__________________ test_revision_allowed_tdd_with_red_fields ___________________

    def test_revision_allowed_tdd_with_red_fields():
>       ops = _build(_request(criteria=[_tdd_with_dirty_red()]))

tests/test_close_batch.py:943:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-green', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'red_check_run_id': 'rec-runner-red', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None, load_check_run = None, kwargs = {}
loader = <function _matching_loader.<locals>.load at 0x705117aa79a0>

    def _build(request: dict, *, cwd: Path | None = None, load_check_run=None, **kwargs):
        """build_batch with a matching store loader unless one is supplied."""
        loader = load_check_run
        if loader is None and request.get("transition") == "done":
            loader = _matching_loader(request)
>       return close_batch.build_batch(
            request, cwd=cwd, load_check_run=loader, **kwargs
        )
E       TypeError: build_batch() got an unexpected keyword argument 'load_check_run'

tests/test_close_batch.py:115: TypeError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_tdd_revision_without_red_is_request_error
FAILED tests/test_close_batch.py::test_revision_allowed_tdd_with_red_fields
2 failed, 43 deselected in 0.07s
