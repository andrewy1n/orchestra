import pytest

from orchestra.composer.idea import IdeaError, slugify


def test_slugify_lowercases_and_joins_runs_with_one_hyphen():
    assert slugify("  Add   a Roadmap -- view!  ") == "add-a-roadmap-view"


def test_slugify_caps_length_and_trims_the_trailing_hyphen():
    slug = slugify("word " * 30)
    assert len(slug) <= 60
    assert not slug.endswith("-")


def test_slugify_folds_accents_to_ascii():
    assert slugify("Café ideas") == "cafe-ideas"


@pytest.mark.parametrize("title", ["!!!", "日本語", "   "])
def test_slugify_rejects_titles_with_no_usable_characters(title):
    with pytest.raises(IdeaError):
        slugify(title)
