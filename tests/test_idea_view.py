"""Oracle tests for composer:idea in orchestra handoff."""

from __future__ import annotations

import pytest

from canon_support import create, seed_effort
from orchestra import views


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "repo"
    from canon_support import make_project

    project = make_project(root)
    seed_effort(project, "alpha")
    return project


def render(project, view, **kwargs):
    return views.render_view(views.VIEWS[view], views.load_records(project), **kwargs)


def test_r8_handoff_lists_open_ideas_with_effort_under_effort(project):
    create(project, "composer:idea", "later-idea", {"effort": "alpha", "status": "open"})
    create(project, "composer:idea", "done-idea", {"effort": "alpha", "status": "dismissed"})
    create(project, "composer:idea", "untriaged", {"status": "open"})
    text = render(project, "handoff")
    assert "### Backlog\n- **later-idea**: alpha; open" in text
    assert "done-idea" not in text
    assert "untriaged" not in text
