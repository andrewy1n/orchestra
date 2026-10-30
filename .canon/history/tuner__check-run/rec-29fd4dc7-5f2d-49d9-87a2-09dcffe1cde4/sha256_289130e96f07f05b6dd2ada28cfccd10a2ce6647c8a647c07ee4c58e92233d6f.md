---
{
  "id": "rec-29fd4dc7-5f2d-49d9-87a2-09dcffe1cde4",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-92ed9b89-080c-4c82-bb49-b9bf2b235c81",
    "duration_s": 0.616358,
    "effort": "canon-db-store",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/canon/test_backend_boundary.py::test_external_modules_do_not_open_store_files"
    ],
    "informed_by": [
      "rec-92ed9b89-080c-4c82-bb49-b9bf2b235c81"
    ],
    "method": "tdd",
    "output_sha256": "e686c0a72df0a0474bf882b9df68d64c4a50a3878d89c86412cc2c1cc7a2383c",
    "requirement": "R11",
    "result": "fail",
    "revision": "0735e6a72f73640ba7c7aea699c9b72f3355b758",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T08:44:59+00:00",
  "relationships": {},
  "revision": "sha256:289130e96f07f05b6dd2ada28cfccd10a2ce6647c8a647c07ee4c58e92233d6f",
  "subject": "store-consumers-r11"
}
---

F.....                                                                   [100%]
=================================== FAILURES ===================================
________________ test_external_modules_do_not_open_store_files _________________

    def test_external_modules_do_not_open_store_files() -> None:
        hits = [
            f"{path.relative_to(ROOT)}:{hit}"
            for path in _outside_sources()
            for hit in _boundary_hits(path.read_text(), inside_canon=False)
            if "imports Store" not in hit
        ]
>       assert not hits, "R11: use Project instead of store file IO:\n" + "\n".join(hits)
E       AssertionError: R11: use Project instead of store file IO:
E         orchestra/cli.py:817: performs store file IO (is_file)
E         orchestra/cli.py:807: performs store file IO (mkdir)
E         orchestra/conductor/suite.py:142: performs store file IO (read_text)
E         dashboard/backend/store.py:35: traverses store files
E       assert not ['orchestra/cli.py:817: performs store file IO (is_file)', 'orchestra/cli.py:807: performs store file IO (mkdir)', 'or...ra/conductor/suite.py:142: performs store file IO (read_text)', 'dashboard/backend/store.py:35: traverses store files']

tests/canon/test_backend_boundary.py:470: AssertionError
=========================== short test summary info ============================
FAILED tests/canon/test_backend_boundary.py::test_external_modules_do_not_open_store_files
1 failed, 5 passed in 0.39s
