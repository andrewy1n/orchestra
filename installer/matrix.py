"""Load and validate the provider matrix."""

from __future__ import annotations

import json
from pathlib import Path

from installer.model import Provider

MATRIX_PATH = Path(__file__).resolve().with_name("providers.json")


class MatrixError(ValueError):
    """The provider matrix is missing or malformed."""


def load_matrix(path: Path | None = None) -> tuple[Provider, ...]:
    """Read ``providers.json`` into immutable :class:`Provider` rows."""
    matrix_path = Path(path) if path is not None else MATRIX_PATH
    try:
        document = json.loads(matrix_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MatrixError(f"cannot read provider matrix {matrix_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise MatrixError(f"provider matrix {matrix_path} is not valid JSON: {exc}") from exc

    if document.get("version") != 1:
        raise MatrixError(f"provider matrix {matrix_path} has unsupported version")
    rows = document.get("providers")
    if not isinstance(rows, list) or not rows:
        raise MatrixError(f"provider matrix {matrix_path} has no providers")

    providers: list[Provider] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise MatrixError(f"provider row {index} is not an object")
        missing = [
            key
            for key in ("id", "name", "kind", "project_root", "global_root")
            if not row.get(key)
        ]
        if missing:
            raise MatrixError(f"provider row {index} is missing {', '.join(missing)}")
        provider_id = str(row["id"])
        if provider_id in seen:
            raise MatrixError(f"provider matrix lists {provider_id!r} twice")
        seen.add(provider_id)
        if row["kind"] not in ("native", "skills"):
            raise MatrixError(
                f"provider {provider_id!r} has unknown kind {row['kind']!r}"
            )
        detect = row.get("detect", [])
        if not isinstance(detect, list):
            raise MatrixError(f"provider {provider_id!r} detect must be a list")
        providers.append(
            Provider(
                id=provider_id,
                name=str(row["name"]),
                kind=str(row["kind"]),
                project_root=str(row["project_root"]),
                global_root=str(row["global_root"]),
                skills_subdir=str(row.get("skills_subdir", "skills")),
                profile=str(row["profile"]) if row.get("profile") else None,
                detect=tuple(str(item) for item in detect),
            )
        )
    return tuple(providers)


def provider_ids(providers: tuple[Provider, ...]) -> tuple[str, ...]:
    return tuple(provider.id for provider in providers)
