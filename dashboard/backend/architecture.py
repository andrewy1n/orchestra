"""The architecture view the dashboard serves."""

from __future__ import annotations

from dashboard.backend import store
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.tools.git import Git
from orchestra.views.architecture import architecture_view


def load_architecture(target: Project, scope: str | None = None, revision: str = "") -> JsonObject:
    return architecture_view(
        store.catalog_records(target), scope, revision or Git(target.project_root).head()
    )
