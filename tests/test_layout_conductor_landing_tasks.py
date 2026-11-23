from tests.layout_support import ROOT, layout_problems, parse_map

SLICE = parse_map(
    {
        "landing": "landing gate land record_scan github_pr github_evidence merge_evidence",
        "tasks": "wave land_task task_landing task_detail assignment execution_cost verification",
        "tasks.close": "task_close close_batch",
        "tasks.redispatch": "task_redispatch redispatch_facts",
    }
)


def test_conductor_landing_and_task_modules_sit_in_their_packages_and_none_remain_at_the_old_path():
    assert layout_problems("conductor", SLICE) == []


def test_landing_module_is_replaced_by_the_landing_package():
    assert not (ROOT / "orchestra" / "conductor" / "landing.py").is_file()
