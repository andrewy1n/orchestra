from tests.layout_support import ROOT, layout_problems, parse_map

SLICE = parse_map(
    {
        "phases.progress": "phase_progress close phase_analysis effort_status release_facts attention activity assessment_facts",
        "phases.workflow": "workflow workflow_review signoff run_record",
    }
)


def test_conductor_phase_modules_sit_in_their_packages_and_none_remain_at_the_old_path():
    assert layout_problems("conductor", SLICE) == []


def test_conductor_root_holds_only_shared_types_and_the_operation_packages():
    root = ROOT / "orchestra" / "conductor"
    entries = {path.name for path in root.iterdir() if path.name != "__pycache__"}
    assert entries == {
        "__init__.py",
        "model_types.py",
        "workspace_types.py",
        "briefs",
        "cli",
        "schemas",
        "verification",
        "landing",
        "tasks",
        "phases",
    }
