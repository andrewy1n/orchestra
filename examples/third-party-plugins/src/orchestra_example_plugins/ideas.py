from __future__ import annotations

from orchestra.composer.idea_source import IdeaSourceItem, IdeaSourceRequest


class Source:
    def list_ideas(self, request: IdeaSourceRequest) -> tuple[IdeaSourceItem, ...]:
        project = request.parameters.get("project", "demo")
        if not isinstance(project, str):
            raise ValueError("project must be a string")
        return (
            IdeaSourceItem(
                external_id="example-1",
                title="Example plugin idea",
                body="Returned by the installed example plugin.",
                url=f"https://example.test/{project}/ideas/1",
                updated_at="2026-11-03T09:00:00Z",
                labels=("example",),
            ),
        )
