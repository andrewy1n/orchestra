from tests.layout_support import layout_problems, parse_map

SCORE = parse_map(
    {
        "planning": "phase work_item acceptance requirements milestone effort effort_rollup autonomy plan_shape scope touches executor oracle_policy analyze",
        "workflow": "workflow_blockers workflow_reviews workflow_selection continuity",
        "facts": "work_item_facts view_facts workspace_facts detail_facts elapsed",
    }
)


def test_score_modules_sit_in_their_packages_and_none_remain_at_the_old_path():
    assert layout_problems("score", SCORE) == []
