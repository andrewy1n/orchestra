"""Shared Git revision comparison rules for Conductor evidence."""

from __future__ import annotations


def revision_matches(check_revision: str, phase_head: str) -> bool:
    check = check_revision.strip().lower()
    head = phase_head.strip().lower()
    if not check or not head:
        return False
    if check == head:
        return True
    shorter, longer = (check, head) if len(check) < len(head) else (head, check)
    return len(shorter) >= 7 and longer.startswith(shorter)
