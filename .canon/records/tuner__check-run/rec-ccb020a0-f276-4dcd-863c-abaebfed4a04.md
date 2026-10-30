---
{
  "id": "rec-ccb020a0-f276-4dcd-863c-abaebfed4a04",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-c1d8f048-f635-4da0-b946-76b4286f631a",
    "diff_sha256": "e5d73803a665c6dae1cdcde7ec7cb26ed6f7c42347ecf2e92b2d52fdf7ac6796",
    "duration_s": 0.512462,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_init_place_step.py::test_engage_routing_line_carries_area"
    ],
    "informed_by": [
      "rec-c1d8f048-f635-4da0-b946-76b4286f631a"
    ],
    "method": "tdd",
    "output_sha256": "15b431697119496b1a669d58ee6f747266bf5b465a28908d04426f79e5e5f894",
    "requirement": "R15",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T07:36:09+00:00",
  "relationships": {},
  "revision": "sha256:f2d09730d81a8ffe3b8fdf2b65f3a53e3de9241a1b9a6d3601960e18b0b8d837",
  "subject": "fix-engage-place-hook-routing"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________________ test_engage_routing_line_carries_area _____________________

    def test_engage_routing_line_carries_area():
        text = (REPO_ROOT / "skills" / "engage" / "SKILL.md").read_text()
        block = ROUTING_BLOCK.search(text)
        assert block, "engage skill has no routing line block"
>       assert re.search(r"^\s*area: ", block.group(1), re.M), block.group(1)
E       AssertionError:    kind: <kind>
E            focus: <effort-slug> (existing | new)
E            phase: <phase-slug> | new | none
E            idea: <subject> | none
E            records: yes | no
E            next: <skill or "this chat">
E
E       assert None
E        +  where None = <function search at 0x7df0012ad510>('^\\s*area: ', '   kind: <kind>\n   focus: <effort-slug> (existing | new)\n   phase: <phase-slug> | new | none\n   idea: <subject> | none\n   records: yes | no\n   next: <skill or "this chat">\n   ', re.MULTILINE)
E        +    where <function search at 0x7df0012ad510> = re.search
E        +    and   '   kind: <kind>\n   focus: <effort-slug> (existing | new)\n   phase: <phase-slug> | new | none\n   idea: <subject> | none\n   records: yes | no\n   next: <skill or "this chat">\n   ' = <built-in method group of re.Match object at 0x7deffeaac9d0>(1)
E        +      where <built-in method group of re.Match object at 0x7deffeaac9d0> = <re.Match object; span=(6472, 6739), match='Show the routing line, then follow that skill wit>.group
E        +    and   re.MULTILINE = re.M

tests/test_init_place_step.py:26: AssertionError
=========================== short test summary info ============================
FAILED tests/test_init_place_step.py::test_engage_routing_line_carries_area
1 failed in 0.05s
