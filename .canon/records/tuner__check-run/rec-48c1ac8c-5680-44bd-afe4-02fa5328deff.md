---
{
  "id": "rec-48c1ac8c-5680-44bd-afe4-02fa5328deff",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-29938747-c59e-4421-838e-0a6c7573a4cb",
    "duration_s": 0.726225,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_skill_evidence_boundary.py::test_migrated_skills_pass_the_scanner"
    ],
    "informed_by": [
      "rec-29938747-c59e-4421-838e-0a6c7573a4cb",
      "rec-0b3a4903-fb7e-474b-ac57-bda7ab086592"
    ],
    "method": "tdd",
    "output_sha256": "02daa95c67d318ec03b8cfbc5fced11b2297beb40b105c074fcb60a6d20ee9b8",
    "requirement": "R5",
    "result": "fail",
    "revision": "2df7598d15159946435617cd150ab4d4dd9329c8",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-orchestration-split-boundary"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-17T08:30:39+00:00",
  "relationships": {},
  "revision": "sha256:e4edabbd804033f3a9ac65a9ba20051bcbcb3adacd9d824b2fb093207545e48b",
  "subject": "verify-orchestration-split-boundary",
  "time": {
    "observed": "2026-10-17T08:30:39+00:00",
    "recorded": "2026-10-17T08:30:39+00:00"
  }
}
---

..F                                                                      [100%]
=================================== FAILURES ===================================
____________________ test_migrated_skills_pass_the_scanner _____________________

    def test_migrated_skills_pass_the_scanner():
        violations = scan_skills(SKILLS)
>       assert not violations, "\n".join(violations)
E       AssertionError: execute-phase/SKILL.md: create project:oracle-amendment
E         execute-phase/SKILL.md: supersede project:oracle-amendment
E       assert not ['execute-phase/SKILL.md: create project:oracle-amendment', 'execute-phase/SKILL.md: supersede project:oracle-amendment']

tests/test_skill_evidence_boundary.py:172: AssertionError
=========================== short test summary info ============================
FAILED tests/test_skill_evidence_boundary.py::test_migrated_skills_pass_the_scanner
1 failed, 2 passed, 1 deselected in 0.05s
