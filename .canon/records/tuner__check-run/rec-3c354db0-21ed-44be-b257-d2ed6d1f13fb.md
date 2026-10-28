---
{
  "id": "rec-3c354db0-21ed-44be-b257-d2ed6d1f13fb",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-89ad5e83-bcbf-41b5-9a8b-87c895807253",
    "diff_sha256": "b35f6778df10d13377619ead13c3951cd5a348e250674efa9b5927fb633691c8",
    "duration_s": 1.285893,
    "effort": "composer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_idea_dashboard.py::test_r9_dashboard_backlog_panel_lists_open_ideas_grouped_by_effort"
    ],
    "informed_by": [
      "rec-89ad5e83-bcbf-41b5-9a8b-87c895807253"
    ],
    "method": "tdd",
    "output_sha256": "487abd4313770dadd5412b49d1083a93bb7afad83de9180a7c05d5ff8fbfa643",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T06:08:58+00:00",
  "relationships": {},
  "revision": "sha256:7f39aad56e9cb90c8087dbb42ebd6ef980ef4e7b3dd8aa85dc27a41b337c1d4e",
  "subject": "idea-dashboard-switch"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______ test_r9_dashboard_backlog_panel_lists_open_ideas_grouped_by_effort ______

store = PosixPath('/tmp/se-workflow-test-c_hecqft')
cli = <function cli.<locals>._run at 0x7305f6e89620>
defs = {'conductor:failed-attempt': {'id': 'conductor:failed-attempt', 'name': 'failed-attempt', 'purpose': 'An approach that...gnment': {'ref': 'conductor:assignment'}, 'result': {'type': 'string'}, 'verdict': {'type': 'string'}, ...}, ...}, ...}

    def test_r9_dashboard_backlog_panel_lists_open_ideas_grouped_by_effort(store, cli, defs):
        _goal(cli, defs, "alpha")
        _goal(cli, defs, "beta")
        open_a = _idea(cli, defs, "park-a", "alpha", body="## Note\n\ndo alpha later")
        _idea(cli, defs, "park-b", "beta", body="## Note\n\ndo beta later")
        promoted = _idea(cli, defs, "park-promoted", "alpha")
        cli(
            "supersede", "--type", "composer:idea", "--id", promoted["id"],
            "--expected-revision", "@current",
            "--payload", json.dumps({"effort": "alpha", "status": "promoted"}),
        )
        dismissed = _idea(cli, defs, "park-dismissed", "alpha")
        cli(
            "supersede", "--type", "composer:idea", "--id", dismissed["id"],
            "--expected-revision", "@current",
            "--payload", json.dumps({"effort": "alpha", "status": "dismissed"}),
        )

        snapshot = model.load_snapshot(_target(store))
        alpha = _effort(snapshot, "alpha")
        beta = _effort(snapshot, "beta")
>       assert [item.subject for item in alpha.backlog] == ["park-a"]
E       AssertionError: assert [] == ['park-a']
E
E         Right contains one more item: 'park-a'
E         Use -v to get more diff

tests/test_idea_dashboard.py:108: AssertionError
=========================== short test summary info ============================
FAILED tests/test_idea_dashboard.py::test_r9_dashboard_backlog_panel_lists_open_ideas_grouped_by_effort
1 failed in 1.01s
