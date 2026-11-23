from tests.layout_support import ROOT, layout_problems, parse_map

VERIFICATION = parse_map(
    {
        "verification.evidence": "head_evidence revision oracle_freeze acceptance_amendment evidence",
        "verification": "check policy verification requirements evidence_recovery",
        "verification.suite": "suite suite_label suite_worker",
        "verification.review": "reviewer review_technique review_brief",
    }
)


def test_conductor_verification_modules_sit_in_their_packages_and_none_remain_at_the_old_path():
    assert layout_problems("conductor", VERIFICATION) == []


def test_verification_module_is_replaced_by_the_verification_package():
    assert not (ROOT / "orchestra" / "conductor" / "verification.py").is_file()
