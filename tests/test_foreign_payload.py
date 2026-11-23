"""A component does not read payload fields of record types it does not own.

The scan follows literal reads only: `payload["key"]` and `payload.get("key")` on a receiver
named `payload` (a name or an attribute). A key is foreign when only another component's schema
types define it. Indirect reads, such as a key held in a variable or a payload passed to a helper,
are not followed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.foreign_payload_support import (
    foreign_reads,
    load_allowlist,
    owner_map,
    scan_package,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "orchestra"
ALLOWLIST = Path(__file__).with_name("foreign_payload_allowlist.txt")


def _allowlist() -> list[str]:
    return load_allowlist(ALLOWLIST)


def test_foreign_payload_reads_match_frozen_allowlist():
    found = scan_package(PACKAGE, owner_map(PACKAGE))
    allowed = set(_allowlist())
    new = sorted(found - allowed)
    stale = sorted(allowed - found)
    assert not new, f"foreign payload reads not in the allowlist: {new}"
    assert not stale, f"stale allowlist entries, remove them: {stale}"


def test_allowlist_is_sorted_and_unique():
    entries = _allowlist()
    assert entries == sorted(set(entries))


def test_seeded_foreign_read_is_flagged():
    owners = {"verify_command": {"score"}, "scope": {"score"}, "attempts": {"tuner"}}
    source = (
        "def run(payload):\n"
        "    a = payload['verify_command']\n"
        "    b = payload.get('scope')\n"
        "    c = payload['attempts']\n"
        "    d = payload['unknown']\n"
    )
    assert foreign_reads(source, "tuner", "orchestra.tuner.seed", owners) == {
        "orchestra.tuner.seed verify_command",
        "orchestra.tuner.seed scope",
    }


def test_key_shared_by_two_components_is_not_flagged():
    owners = {"effort": {"score", "conductor"}}
    source = "def run(payload):\n    return payload['effort']\n"
    assert foreign_reads(source, "tuner", "orchestra.tuner.seed", owners) == set()


def test_indirect_reads_are_not_followed():
    owners = {"verify_command": {"score"}}
    source = "def run(payload):\n    key = 'verify_command'\n    return payload[key]\n"
    assert foreign_reads(source, "tuner", "orchestra.tuner.seed", owners) == set()


def test_missing_allowlist_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_allowlist(tmp_path / "absent.txt")
