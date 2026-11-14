from __future__ import annotations

import pytest

from orchestra.conductor.reviewer import (
    revision_matches as reviewer_match,
)
from orchestra.conductor.revision import revision_matches


@pytest.mark.parametrize(
    ("checked", "head", "expected"),
    [
        pytest.param(" abcdef0 ", "ABCDEF0123", True, id="r1_whitespace"),
        pytest.param("abcdef0", "ABCDEF0123", True, id="r2_case"),
        pytest.param("", "abcdef0123", False, id="r3_empty_checked"),
        pytest.param("abcdef0", "", False, id="r3_empty_head"),
        pytest.param("abcd", "ABCD", True, id="r4_exact_short"),
        pytest.param("abcdef0", "abcdef0123", True, id="r5_prefix_checked_shorter"),
        pytest.param("abcdef0123", "abcdef0", True, id="r5_prefix_head_shorter"),
        pytest.param("abcdef01", "abcdef0123", True, id="r5_longer_prefix_checked_shorter"),
        pytest.param("abcdef0123", "abcdef01", True, id="r5_longer_prefix_head_shorter"),
        pytest.param("abcdef", "abcdef0123", False, id="r6_short_prefix"),
        pytest.param("abcdef0123", "ghijklmnop", False, id="r7_unrelated"),
    ],
)
def test_revision_policy(checked: str, head: str, expected: bool) -> None:
    assert revision_matches(checked, head) is expected


@pytest.mark.parametrize(
    ("checked", "head", "expected"),
    [
        pytest.param("abcdef0", "abcdef0123", True, id="seven_character_prefix"),
        pytest.param("abcdef01", "abcdef0123", True, id="longer_prefix"),
        pytest.param("abcdef", "abcdef0123", False, id="six_character_prefix"),
        pytest.param("ABcdef0", "abcdef0123", True, id="normalized_prefix"),
    ],
)
def test_suite_and_reviewer_use_shared_policy(
    checked: str,
    head: str,
    expected: bool,
) -> None:
    assert reviewer_match(checked, head) is expected
