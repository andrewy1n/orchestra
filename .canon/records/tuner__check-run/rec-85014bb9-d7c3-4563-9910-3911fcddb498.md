---
{
  "id": "rec-85014bb9-d7c3-4563-9910-3911fcddb498",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-947d7fdd-45f6-422a-88f5-a8d67a2a3d4a",
    "diff_sha256": "fd9d7734ac9e10abb19025f20ecd0ffc9dfadc3930054f8bc9274db2bef7453d",
    "duration_s": 0.263486,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_effort_brief_skills.py::test_r13_score_agents_lists_brief_among_the_types"
    ],
    "informed_by": [
      "rec-947d7fdd-45f6-422a-88f5-a8d67a2a3d4a"
    ],
    "method": "tdd",
    "output_sha256": "34dd3f53069fa5a3c72fabc900ad6750197b8686ed2d4d72559fe1ba3aaf085b",
    "requirement": "R13",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T17:07:53+00:00",
  "relationships": {},
  "revision": "sha256:560ee97dfbeec169a4fa5c76ba4fc3fa6ac9e4e84b7315b5344fbaebbe3ce2ca",
  "subject": "brief-skills-r13"
}
---

F                                                                                                                                                                                                                                                  [100%]
======================================================================================================================== FAILURES ========================================================================================================================
___________________________________________________________________________________________________ test_r13_score_agents_lists_brief_among_the_types ____________________________________________________________________________________________________

    def test_r13_score_agents_lists_brief_among_the_types():
        text = _flat(SCORE_AGENTS.read_text())
        listed = re.search(r"\(([^)]*\beffort\b[^)]*)\)", text)
        assert listed
>       assert re.search(r"\bbrief\b", listed.group(1))
E       AssertionError: assert None
E        +  where None = <function search at 0x7c4bf35154e0>('\\bbrief\\b', 'effort, position, milestone, phase, specification, design, decision, constraint, work-item, acceptance, continuity-question')
E        +    where <function search at 0x7c4bf35154e0> = re.search
E        +    and   'effort, position, milestone, phase, specification, design, decision, constraint, work-item, acceptance, continuity-question' = <built-in method group of re.Match object at 0x7c4bf26af640>(1)
E        +      where <built-in method group of re.Match object at 0x7c4bf26af640> = <re.Match object; span=(49, 174), match='(effort, position, milestone, phase, specificatio>.group

tests/test_effort_brief_skills.py:65: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_effort_brief_skills.py::test_r13_score_agents_lists_brief_among_the_types - AssertionError: assert None
1 failed, 4 deselected in 0.04s
