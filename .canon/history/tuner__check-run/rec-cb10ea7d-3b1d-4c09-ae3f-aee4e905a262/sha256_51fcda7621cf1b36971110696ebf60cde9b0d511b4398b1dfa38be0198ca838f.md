---
{
  "id": "rec-cb10ea7d-3b1d-4c09-ae3f-aee4e905a262",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-03b0ee08-8958-4e55-ad67-94993e971b8e",
    "diff_sha256": "3b751b530ab9dc4a00607f3151fef4fc8805f6d54ffb955ef97ee533bf8c1910",
    "duration_s": 0.511607,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_engage_place_step.py::test_engage_skill_names_orchestra_place"
    ],
    "informed_by": [
      "rec-03b0ee08-8958-4e55-ad67-94993e971b8e"
    ],
    "method": "tdd",
    "output_sha256": "36115f8ca3c999022734286e277836a5c927206616d27f9b91c2c209ad81eaea",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T06:56:49+00:00",
  "relationships": {},
  "revision": "sha256:51fcda7621cf1b36971110696ebf60cde9b0d511b4398b1dfa38be0198ca838f",
  "subject": "engage-place-step"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________ test_engage_skill_names_orchestra_place ____________________

    def test_engage_skill_names_orchestra_place():
        text = (REPO_ROOT / "skills" / "engage" / "SKILL.md").read_text()
>       assert "orchestra place" in text
E       AssertionError: assert 'orchestra place' in '---\nname: engage\ndescription: >-\n  Classifies a software-engineering ask as deliver, repair, evaluate,\n  or incid...rsede another subject’s goal or position\n- Write work-items here\n- Promote an idea from engage\n- Add a fifth kind\n'

tests/test_engage_place_step.py:8: AssertionError
=========================== short test summary info ============================
FAILED tests/test_engage_place_step.py::test_engage_skill_names_orchestra_place
1 failed in 0.05s
