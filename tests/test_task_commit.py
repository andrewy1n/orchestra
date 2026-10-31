"""execute-phase requires a commit per task before verify.

Skill commit snippets use a Conventional Commits subject,
``type(scope): summary``, where type is feat, fix, docs, refactor, test,
or chore. The body is one or two sentences on why. A subject with an
empty body does not satisfy this. A task commit names the task slug in
the body.
"""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"

_TYPES = "feat|fix|docs|refactor|test|chore"
_SUBJECT = re.compile(rf"^(?:{_TYPES})\([^()\s]+\): \S.*$")
_FENCE_RE = re.compile(r"```[a-z]*\n(.*?)```", re.DOTALL)
_HEREDOC_COMMIT_RE = re.compile(
    r"""commit -m "\$\(cat <<'EOF'\n(.*?)\nEOF\n\)\"""",
    re.DOTALL,
)
_QUOTED_COMMIT_RE = re.compile(r'commit -m "([^"]*)"')


def _text() -> str:
    return re.sub(r"\s+", " ", SKILL.read_text())


def _body_names_task_slug(message: str) -> bool:
    parts = message.strip().split("\n\n", 1)
    body = parts[1] if len(parts) == 2 else ""
    return "<task-slug>" in body


def conventional_commit(message: str) -> bool:
    """True when message is type(scope): summary plus one or two sentences."""
    parts = message.strip().split("\n\n")
    if len(parts) != 2:
        return False
    subject, body = parts[0].strip(), parts[1].strip()
    if "\n" in subject or "\n" in body or not body or not _SUBJECT.fullmatch(subject):
        return False
    sentences = re.findall(r"[^.!?]+[.!?]", body)
    return "".join(sentences) == body and 1 <= len(sentences) <= 2


def _fence_commits(fence: str) -> list[str]:
    spans: list[tuple[int, int]] = []
    found: list[tuple[int, str]] = []
    for match in _HEREDOC_COMMIT_RE.finditer(fence):
        found.append((match.start(), match.group(1).strip()))
        spans.append(match.span())
    for match in _QUOTED_COMMIT_RE.finditer(fence):
        if any(start <= match.start() < end for start, end in spans):
            continue
        found.append((match.start(), match.group(1).strip()))
    found.sort(key=lambda item: item[0])
    return [message for _, message in found]


def commit_messages(path: Path) -> list[str]:
    messages: list[str] = []
    for fence in _FENCE_RE.findall(path.read_text()):
        messages.extend(_fence_commits(fence))
    return messages


def test_execute_phase_requires_a_commit_per_task_before_verify():
    text = _text()
    assert "after each task's code lands and before verify" in text
    assert "commit per task" in text
    assert "passing check-run can carry a real SHA" in text


def test_task_commit_excludes_artifacts_on_the_phase_branch():
    text = _text()
    assert "<repo>/.worktrees/<phase-slug>--<task-slug>" in text
    assert "That commit excludes `.canon`" in text
    assert "add -A -- . ':!.canon'" in text


def test_subject_with_an_empty_body_fails():
    assert conventional_commit("feat(scope): summary\n\nWhy this change is made.")
    assert conventional_commit("fix(scope): summary\n\nFirst reason. Second reason.")
    assert not conventional_commit("feat(scope): summary")
    assert not conventional_commit("feat(scope): summary\n")
    assert not conventional_commit("feat(scope): summary\n\n")
    assert not conventional_commit("feat(scope): summary\n\n   ")
    assert not conventional_commit("chore(records): <what changed>")
    assert not conventional_commit("feat(scope): summary\n\nOne. Two. Three.")


def test_execute_phase_snippets_match_conventional_commits():
    messages = commit_messages(SKILL)
    named = [message for message in messages if _body_names_task_slug(message)]
    assert named
    assert all(conventional_commit(message) for message in named)
    assert all(conventional_commit(message) for message in messages)


def test_task_commit_body_names_the_task_slug():
    named = [message for message in commit_messages(SKILL) if _body_names_task_slug(message)]
    assert named
    assert all(conventional_commit(message) for message in named)


def test_r27_per_task_commit_path_is_the_task_worktree():
    text = _text()
    assert "git -C <repo>/.worktrees/<phase-slug>--<task-slug> commit" in text
