---
{
  "base_kind": "event",
  "id": "rec-67d02bcd-6f63-46b9-ae30-afeddad6f3b6",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-a4a45232-6634-47b1-bbaf-11633085234e",
    "diff_sha256": "b1d411a3b1f8d7207a47f57915c3c7751f53d016a96f1f803a0237e9357964f2",
    "duration_s": 0.682655,
    "effort": "workflow-loop",
    "exit_code": 1,
    "method": "tdd",
    "output_sha256": "c49b4909188d556f80e9750225288f7293317b5e8f49ec86ffc647ae3bd78a2a",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "close-batch-store-verify"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-16T09:42:21+00:00",
  "relationships": {
    "informed_by": [
      "rec-a4a45232-6634-47b1-bbaf-11633085234e",
      "rec-2da27c78-39a7-46cb-9580-6d3532c70b7d"
    ]
  },
  "revision": "sha256:4207cad70e160e9dd788ea604ed1f0b4ed46aabc52e69338b293efadbec07e95",
  "subject": "close-batch-store-verify",
  "time": {
    "observed": "2026-10-16T09:42:21+00:00",
    "recorded": "2026-10-16T09:42:21+00:00"
  }
}
---

h pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
>           _build(request, load_check_run=missing)

tests/test_close_batch.py:804:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-green', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'red_check_run_id': 'rec-runner-red', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None
load_check_run = <function test_store_authority_refuses_fabricated_check_run_id.<locals>.missing at 0x70414c8db910>
kwargs = {}
loader = <function test_store_authority_refuses_fabricated_check_run_id.<locals>.missing at 0x70414c8db910>

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
___________ test_store_authority_refuses_fabricated_red_check_run_id ___________

    def test_store_authority_refuses_fabricated_red_check_run_id():
        request = _request(criteria=[_tdd_with_dirty_red()])
        base = _matching_loader(request)

        def green_only(cid: str) -> dict:
            if cid == "rec-runner-red":
                raise LookupError(cid)
            return base(cid)

        with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
>           _build(request, load_check_run=green_only)

tests/test_close_batch.py:818:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-green', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'red_check_run_id': 'rec-runner-red', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None
load_check_run = <function test_store_authority_refuses_fabricated_red_check_run_id.<locals>.green_only at 0x70414c8dbe20>
kwargs = {}
loader = <function test_store_authority_refuses_fabricated_red_check_run_id.<locals>.green_only at 0x70414c8dbe20>

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
_________________ test_store_authority_mismatch_result_refuses _________________

    def test_store_authority_mismatch_result_refuses():
        request = _request(criteria=[_tdd_with_dirty_red()])
        base = _matching_loader(request)

        def wrong_result(cid: str) -> dict:
            rec = base(cid)
            if cid == "rec-runner-green":
                rec = {
                    "id": cid,
                    "payload": {**rec["payload"], "result": "fail"},
                }
            return rec

        with pytest.raises(close_batch.CloseRefused, match="mismatch") as excinfo:
>           _build(request, load_check_run=wrong_result)

tests/test_close_batch.py:836:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-green', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'red_check_run_id': 'rec-runner-red', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None
load_check_run = <function test_store_authority_mismatch_result_refuses.<locals>.wrong_result at 0x70414c8db880>
kwargs = {}
loader = <function test_store_authority_mismatch_result_refuses.<locals>.wrong_result at 0x70414c8db880>

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
________________ test_store_authority_mismatch_revision_refuses ________________

    def test_store_authority_mismatch_revision_refuses():
        request = _request(criteria=[_tdd_with_dirty_red()])
        base = _matching_loader(request)

        def wrong_revision(cid: str) -> dict:
            rec = base(cid)
            if cid == "rec-runner-green":
                rec = {
                    "id": cid,
                    "payload": {**rec["payload"], "revision": "otherrev"},
                }
            return rec

        with pytest.raises(close_batch.CloseRefused, match="mismatch") as excinfo:
>           _build(request, load_check_run=wrong_revision)

tests/test_close_batch.py:854:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

request = {'acceptance_ids': ['rec-ac1'], 'criteria': [{'check_run_id': 'rec-runner-green', 'criterion_id': 'rec-ac1', 'method': 'tdd', 'red_check_run_id': 'rec-runner-red', ...}], 'effort': 'effort-1', 'execution_report_id': 'rec-er', ...}
cwd = None
load_check_run = <function test_store_authority_mismatch_revision_refuses.<locals>.wrong_revision at 0x70414c918430>
kwargs = {}
loader = <function test_store_authority_mismatch_revision_refuses.<locals>.wrong_revision at 0x70414c918430>

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
_____________ test_cli_store_authority_fabricated_writes_no_batch ______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-144/test_cli_store_authority_fabri0')

    def test_cli_store_authority_fabricated_writes_no_batch(tmp_path):
        result, out_path = _run_script(_request(), tmp_path)
>       assert result.returncode == 2
E       AssertionError: assert 0 == 2
E        +  where 0 = CompletedProcess(args=['/usr/bin/python3', '/home/andrewyin/affidavit--claim-witnesses/bin/aff', 'close-batch', '--inp...ytest-of-andrewyin/pytest-144/test_cli_store_authority_fabri0/close-batch.ndjson'], returncode=0, stdout='', stderr='').returncode

tests/test_close_batch.py:860: AssertionError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_cli_fabricated_check_run_id_exits_2_and_writes_no_file
FAILED tests/test_close_batch.py::test_store_authority_refuses_fabricated_check_run_id
FAILED tests/test_close_batch.py::test_store_authority_refuses_fabricated_red_check_run_id
FAILED tests/test_close_batch.py::test_store_authority_mismatch_result_refuses
FAILED tests/test_close_batch.py::test_store_authority_mismatch_revision_refuses
FAILED tests/test_close_batch.py::test_cli_store_authority_fabricated_writes_no_batch
6 failed, 39 deselected in 0.20s
