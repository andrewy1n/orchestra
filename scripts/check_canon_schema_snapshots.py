"""Check the repository's Canon schema snapshots from the checkout root."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _check_snapshot(namespace: str, package: object) -> str | None:
    if not isinstance(package, str) or not all(part.isidentifier() for part in package.split(".")):
        return f"{namespace}: invalid schema package {package!r} in pyproject.toml"

    snapshot = Path(".canon", "schemas", f"{namespace}.json")
    shipped = Path(*package.split(".")) / f"{namespace}.json"
    try:
        snapshot_text = snapshot.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"{namespace}: missing schema snapshot {snapshot}"
    except (OSError, UnicodeError) as exc:
        return f"{namespace}: cannot read schema snapshot {snapshot}: {exc}"
    try:
        shipped_text = shipped.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return f"{namespace}: cannot read shipped schema {shipped}: {exc}"

    if snapshot_text != shipped_text:
        return f"{namespace}: stale schema snapshot {snapshot} differs from {shipped}"
    return None


def main() -> int:
    try:
        with Path("pyproject.toml").open("rb") as manifest:
            schemas = tomllib.load(manifest)["project"]["entry-points"]["canon.schemas"]
    except (OSError, ValueError) as exc:
        print(f"cannot read pyproject.toml: {exc}", file=sys.stderr)
        return 1
    except (KeyError, TypeError):
        schemas = None

    if not isinstance(schemas, dict) or not schemas:
        print(
            'pyproject.toml must register schemas in [project.entry-points."canon.schemas"]',
            file=sys.stderr,
        )
        return 1

    failures = [
        error
        for namespace, package in sorted(schemas.items())
        if (error := _check_snapshot(namespace, package)) is not None
    ]
    for failure in failures:
        print(failure, file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
