---
{
  "id": "rec-f7839f02-e3ff-4efd-bc1a-2e37c61e839c",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-73b259a3-7414-471a-869a-49df8f41d5c3",
    "diff_sha256": "fd9d7734ac9e10abb19025f20ecd0ffc9dfadc3930054f8bc9274db2bef7453d",
    "duration_s": 0.275793,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_effort_brief_skills.py::test_r11_init_gives_a_brief_body_template_with_the_four_headings"
    ],
    "informed_by": [
      "rec-73b259a3-7414-471a-869a-49df8f41d5c3"
    ],
    "method": "tdd",
    "output_sha256": "4b8851c8111ed934ca41c1d9f571f97ba7223fb9718a5575d17123750503ecc3",
    "requirement": "R11",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T17:07:49+00:00",
  "relationships": {},
  "revision": "sha256:e17682674490b229f8b5d848141dbd7044ba595150ab270d1a7b0666f62c3144",
  "subject": "brief-skills-r11"
}
---

F                                                                                                                                                                                                                                                  [100%]
======================================================================================================================== FAILURES ========================================================================================================================
____________________________________________________________________________________________ test_r11_init_gives_a_brief_body_template_with_the_four_headings ____________________________________________________________________________________________

    def test_r11_init_gives_a_brief_body_template_with_the_four_headings():
        text = skill_text("init")
>       assert CREATE_BRIEF.search(text)
E       AssertionError: assert None
E        +  where None = <built-in method search of re.Pattern object at 0x1747f500>('---\nname: init\ndescription: >-\n  Adopts the current git repo into the orchestra store: live goal,\n  and a score:p.... Never hand-edit a record file.\n- **Read by relevance.** Route by focus, then phase. Never bulk-read\n  the store.\n')
E        +    where <built-in method search of re.Pattern object at 0x1747f500> = re.compile('canon create --type score:brief\\b').search

tests/test_effort_brief_skills.py:45: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_effort_brief_skills.py::test_r11_init_gives_a_brief_body_template_with_the_four_headings - AssertionError: assert None
1 failed, 4 deselected in 0.04s
