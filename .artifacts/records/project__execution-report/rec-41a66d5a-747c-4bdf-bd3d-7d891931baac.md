---
{
  "base_kind": "observation",
  "id": "rec-41a66d5a-747c-4bdf-bd3d-7d891931baac",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "import-open",
    "result": "pass",
    "revision": "e3fe8e65d40593cda4d782a96e99c75f0e478cef",
    "verdict": "pass",
    "work_item": "import-open"
  },
  "provenance": {
    "sources": [
      "import-open"
    ]
  },
  "record_type": "project:execution-report",
  "recorded_at": "2026-10-22T07:01:34+00:00",
  "relationships": {},
  "revision": "sha256:39110e4e2c3b0dc6f6342ea10ffce1fdce1d857f177580d181974d7c54ebc75e",
  "subject": "import-open",
  "time": {
    "observed": "2026-10-22T07:01:34+00:00",
    "recorded": "2026-10-22T07:01:34+00:00"
  }
}
---

subject: import-open
kind: deliver
result: pass
revision: dirty
evidence: From /home/andrewyin/orchestra/.worktrees/declared-install--import-open, the R7 command (PYTHONPATH=. python3 -c spy on subprocess.run around orchestra.aa.find_store_root with ADAPTIVE_ARTIFACTS_BIN, CLAUDE_PLUGIN_ROOT, and CURSOR_PLUGIN_ROOT unset) exited 0. orchestra/ and dashboard/ have no reads of those variables that choose a store or a binary. README now says the process imports the adaptive-artifacts library.
observations: find_store_root already calls adaptive_artifacts.project.open_store. The README no longer lists $ADAPTIVE_ARTIFACTS_BIN, ~/adaptive-artifacts/bin/adaptive-artifacts, then PATH.
root_cause:
verdict: pass
metrics:
claim: R7: with ADAPTIVE_ARTIFACTS_BIN unset, orchestra opens the store by importing the library.
needs_human: false
attempted_action:
retry_when:
blocker:
