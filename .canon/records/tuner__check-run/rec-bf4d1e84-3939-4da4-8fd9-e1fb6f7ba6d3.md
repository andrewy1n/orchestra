---
{
  "id": "rec-bf4d1e84-3939-4da4-8fd9-e1fb6f7ba6d3",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-5e3ca47a-1650-42a3-8bc8-dc3c01034eb1",
    "duration_s": 0.341451,
    "effort": "canon-db-store",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/canon/test_backend_boundary.py::test_canon_callers_do_not_build_file_backend_paths"
    ],
    "informed_by": [
      "rec-5e3ca47a-1650-42a3-8bc8-dc3c01034eb1"
    ],
    "method": "tdd",
    "output_sha256": "721809719e8fa81778de296d852a487217c2778089d09de054788597f7ae35dd",
    "requirement": "R5",
    "result": "fail",
    "revision": "0735e6a72f73640ba7c7aea699c9b72f3355b758",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T08:44:47+00:00",
  "relationships": {},
  "revision": "sha256:efbf8a920952b2d673bb6caf1fa584ecf91e46740787b85dc43ca877a2332604",
  "subject": "backend-boundary-r5"
}
---

F.....                                                                   [100%]
=================================== FAILURES ===================================
______________ test_canon_callers_do_not_build_file_backend_paths ______________

    def test_canon_callers_do_not_build_file_backend_paths() -> None:
        hits = [
            f"{path.relative_to(ROOT)}:{hit}"
            for path in sorted((ROOT / "orchestra" / "canon").glob("*.py"))
            if path.name not in FILE_BACKEND
            for hit in _boundary_hits(path.read_text(), inside_canon=True)
        ]
>       assert not hits, "R5: file layout must stay in file backend:\n" + "\n".join(hits)
E       AssertionError: R5: file layout must stay in file backend:
E         orchestra/canon/merge.py:197: builds path under store root
E         orchestra/canon/merge.py:208: calls file-layout method record_path
E         orchestra/canon/merge.py:197: builds path under store root
E         orchestra/canon/merge.py:197: builds path under store root
E         orchestra/canon/project.py:283: builds path under store root
E         orchestra/canon/project.py:242: builds path under store root
E         orchestra/canon/schema.py:224: builds path under store root
E         orchestra/canon/schema.py:224: builds path under store root
E         orchestra/canon/sync.py:33: calls file-layout method config_path
E         orchestra/canon/sync.py:73: calls file-layout method snapshot_path
E         orchestra/canon/sync.py:74: calls file-layout method snapshot_path
E         orchestra/canon/sync.py:95: calls file-layout method snapshot_path
E         orchestra/canon/validation.py:256: builds path under store root
E         orchestra/canon/validation.py:342: builds path under store root
E         orchestra/canon/validation.py:364: builds path under store root
E         orchestra/canon/validation.py:419: builds path under store root
E         orchestra/canon/validation.py:342: builds path under store root
E         orchestra/canon/validation.py:364: builds path under store root
E         orchestra/canon/validation.py:279: builds path under store root
E         orchestra/canon/validation.py:342: builds path under store root
E         orchestra/canon/validation.py:364: builds path under store root
E         orchestra/canon/validation.py:534: builds path under store root
E         orchestra/canon/validation.py:279: builds path under store root
E         orchestra/canon/validation.py:534: builds path under store root
E         orchestra/canon/validation.py:279: builds path under store root
E         orchestra/canon/validation.py:534: builds path under store root
E         orchestra/canon/validation.py:534: builds path under store root
E       assert not ['orchestra/canon/merge.py:197: builds path under store root', 'orchestra/canon/merge.py:208: calls file-layout method...non/project.py:283: builds path under store root', 'orchestra/canon/project.py:242: builds path under store root', ...]

tests/canon/test_backend_boundary.py:440: AssertionError
=========================== short test summary info ============================
FAILED tests/canon/test_backend_boundary.py::test_canon_callers_do_not_build_file_backend_paths
1 failed, 5 passed in 0.14s
