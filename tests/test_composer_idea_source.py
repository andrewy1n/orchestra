from __future__ import annotations

import pytest

from orchestra.composer.idea_source import (
    IdeaSource,
    IdeaSourceItem,
    IdeaSourceRequest,
    validate_idea_source_items,
)


class ExampleSource:
    def list_ideas(self, request: IdeaSourceRequest) -> tuple[IdeaSourceItem, ...]:
        return (
            IdeaSourceItem(
                external_id="issue-17",
                title="Add source adapters",
                body="Expose ideas from an installed source.",
                url="https://example.test/issues/17",
                updated_at="2026-11-03T09:00:00Z",
                labels=("composer",),
            ),
        )


def test_idea_source_returns_structured_items_without_store_access() -> None:
    source: IdeaSource = ExampleSource()

    items = validate_idea_source_items(source.list_ideas(IdeaSourceRequest(parameters={})))

    assert items[0].external_id == "issue-17"
    assert items[0].labels == ("composer",)


def test_idea_source_requires_zoned_update_time() -> None:
    item = IdeaSourceItem("1", "Idea", "Body", "https://example.test", "2026-11-03", ())

    with pytest.raises(ValueError, match="time zone"):
        validate_idea_source_items((item,))


@pytest.mark.parametrize("items", ("not-items", ["not-an-item"]))
def test_idea_source_rejects_invalid_item_shapes(items: object) -> None:
    with pytest.raises(ValueError, match="idea source output"):
        validate_idea_source_items(items)
