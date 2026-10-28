import pytest

from canon_support import create, make_project
from orchestra.composer.idea import IdeaError, capture


@pytest.fixture
def project(tmp_path):
    return make_project(tmp_path / "repo")


def _ideas(project):
    return [r for r in project.records() if r["record_type"] == "composer:idea"]


def test_capture_writes_an_open_idea_with_the_title_first_in_the_body(project):
    record = capture(project, "Add a Roadmap", body="More detail.")
    assert record["subject"] == "add-a-roadmap"
    assert record["payload"] == {"status": "open"}
    assert record["body"].splitlines()[0] == "# Add a Roadmap"
    assert record["body"].strip().endswith("More detail.")


def test_capture_refuses_a_duplicate_subject_and_writes_nothing_more(project):
    capture(project, "Same title")
    with pytest.raises(IdeaError):
        capture(project, "Same title")
    assert len(_ideas(project)) == 1


def test_capture_stores_area_and_source(project):
    create(project, "composer:area", "dash", {"title": "Dashboard"}, "## Scope\n\nx")
    record = capture(project, "Placed", area="dash", source="chat")
    assert record["payload"] == {"status": "open", "area": "dash", "source": "chat"}


def test_capture_wraps_an_unknown_area_in_idea_error_and_writes_nothing(project):
    with pytest.raises(IdeaError):
        capture(project, "Lost", area="ghost")
    assert _ideas(project) == []
