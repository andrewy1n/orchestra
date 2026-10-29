---
{
  "id": "rec-596ab96c-947c-451d-8c3d-d0ec6fcbfb37",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "shared-helpers-review",
    "effort": "package-layout",
    "evidence_kind": "review",
    "method": "review",
    "result": "fail",
    "revision": "4cf96460fa33cc3e6c27e3d170f9c4023af84ad4",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T10:15:11+00:00",
  "relationships": {},
  "revision": "sha256:e1728c12ba01e2f81a3a00b4164c28cd213394f285a90ad28cd9fe05d3c58479",
  "subject": "shared-helpers-review"
}
---

verdict: NEEDS_WORK
findings:
  - task: phase
    kind: missing-test
    expected: Specification acceptance requires one test that requests each of the eleven listed API paths from both the stdlib server and the FastAPI app against the same store (R12–R14 acceptance bullet).
    observed: tests/test_shared_helpers.py covers R12–R14 with static AST scans only (test_r12_route_table, test_r13_stdlib_reads_table, test_r14_fastapi_reads_table). Existing HTTP tests (tests/test_web_dashboard.py, tests/test_web_fastapi_writes.py) hit a subset of paths and do not exercise every route on both servers from one parity test.
    severity: major
integration:
  interfaces: orchestra.canon.git_backend.run_git centralizes git argv under orchestra/ and dashboard/; orchestra.canon.record_payload in orchestra/canon/__init__.py is imported by orchestra.views, orchestra.conductor.close_batch, dashboard.model, dashboard.approval, and dashboard.journal. orchestra.conductor.check owns parse_failing_node_ids and _output_sha256; orchestra.conductor.suite imports and uses them. orchestra.tuner.sign is the sole tuner ssh-keygen module; human_claim, amendment, and attestation delegate verify/sign. dashboard.web.routes.ROUTES is iterated by dashboard.web.service (stdlib handler) and dashboard.web.app.create_app (FastAPI).
  assumptions: Phase scope is commits 8077aa4fc..4cf96460f on /home/andrewyin/orchestra/.worktrees/shared-helpers; tests/test_shared_helpers.py oracles match product intent; targeted pytest runs (test_shared_helpers, test_boundaries, test_web_dashboard, test_check, test_tiered_verification) reflect acceptance behavior where run.
  invariants: Canon modules import only orchestra.canon.* (no other orchestra components). No orchestra.conductor imports under orchestra/tuner/. R5 scan passes (git argv literals only in orchestra/canon/git_backend.py). R6/R7 failure policies preserved (rev_parse_token returns None, git_head raises). Eleven-route set unchanged in ROUTES. tests/test_boundaries.py passed.
  conflicts: Specification acceptance calls for HTTP route parity across both servers; the tree proves table wiring statically and partially at runtime, not the full dual-server path matrix in one test.
