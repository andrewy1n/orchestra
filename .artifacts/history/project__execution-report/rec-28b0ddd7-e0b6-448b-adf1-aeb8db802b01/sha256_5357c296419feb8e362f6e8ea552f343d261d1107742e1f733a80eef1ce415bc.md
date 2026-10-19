---
{
  "base_kind": "observation",
  "id": "rec-28b0ddd7-e0b6-448b-adf1-aeb8db802b01",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "oracle-assertion-red",
    "result": "pass",
    "revision": "3c68d691a93d1b37ae562bfb568bb3780eda89fc",
    "verdict": "pass",
    "work_item": "oracle-assertion-red"
  },
  "provenance": {
    "sources": [
      "oracle-assertion-red"
    ]
  },
  "record_type": "project:execution-report",
  "recorded_at": "2026-10-16T20:31:50+00:00",
  "relationships": {},
  "revision": "sha256:5357c296419feb8e362f6e8ea552f343d261d1107742e1f733a80eef1ce415bc",
  "subject": "oracle-assertion-red",
  "time": {
    "observed": "2026-10-16T20:31:50+00:00",
    "recorded": "2026-10-16T20:31:50+00:00"
  }
}
---

subject: oracle-assertion-red
kind: deliver
result: pass
revision: 3c68d691a93d1b37ae562bfb568bb3780eda89fc
evidence: python3 -m pytest tests/test_oracle_red.py tests/test_affidavit_check.py -q -k 'failing_node or assertion_level or oracle_red' → red (ModuleNotFoundError: affidavit.oracle_red) then green (12 passed, 23 deselected); flock commit oracle-assertion-red
observations: added affidavit/oracle_red.py (is_assertion_level_failure / is_assertion_level_red); check.py sets failing_node_ids JSON list on fail via suite.parse_failing_node_ids; tests cover assert→true, import/collection→false, aff check payload
root_cause:
verdict: pass
metrics: 12 passed
claim: assertion-level red classifier and aff check failing_node_ids land at 3c68d69
needs_human: false
attempted_action:
retry_when:
blocker:
