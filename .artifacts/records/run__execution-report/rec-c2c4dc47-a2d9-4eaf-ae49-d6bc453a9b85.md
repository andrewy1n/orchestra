---
{
  "id": "rec-c2c4dc47-a2d9-4eaf-ae49-d6bc453a9b85",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "package-metadata",
    "result": "pass",
    "revision": "eca028601fff7845f1b1cca665f4c09b267878d5",
    "verdict": "pass",
    "work_item": "package-metadata"
  },
  "provenance": {
    "sources": [
      "package-metadata"
    ]
  },
  "record_type": "run:execution-report",
  "recorded_at": "2026-10-22T07:01:34+00:00",
  "relationships": {},
  "revision": "sha256:b0b452951b48a8eb5138e636d37f74e1c18edcde060873d65febf86405a2477a",
  "subject": "package-metadata",
  "time": {
    "observed": "2026-10-22T07:01:34+00:00",
    "recorded": "2026-10-22T07:01:34+00:00"
  }
}
---

subject: package-metadata
kind: deliver
result: pass
revision: dirty
evidence: From the orchestra write root, R1 AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r1_affidavit_depends_on_adaptive_artifacts -q passed (1 passed). R2 python3 -c dependency-chunk assert for adaptive-artifacts exited 0. R3 python3 -c dependency-chunk assert that affidavit is absent exited 0. R4 AFFIDAVIT_ROOT=/home/andrewyin/affidavit/.worktrees/declared-install python3 -m pytest tests/test_declared_install_metadata.py::test_r4_evidence_extra_depends_on_affidavit -q passed (1 passed).
observations: Affidavit worktree pyproject.toml declares adaptive-artifacts @ git+https://github.com/andrewy1n/adaptive-artifacts, setuptools packages = ["affidavit"], and aff = "affidavit.cli:main". Orchestra pyproject.toml uses that same required dependency and adds evidence = ["affidavit @ git+https://github.com/andrewy1n/affidavit"]. Affidavit is not in required dependencies.
root_cause:
verdict: pass
metrics: r1=1 passed; r2=exit 0; r3=exit 0; r4=1 passed
claim: Affidavit depends on adaptive-artifacts; orchestra depends on adaptive-artifacts and, only via the evidence extra, on affidavit.
needs_human: false
attempted_action:
retry_when:
blocker:
