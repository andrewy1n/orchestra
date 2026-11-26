"""Check the installed Canon schemas against the repository snapshot and pin files."""

from __future__ import annotations

import sys
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.metadata import MetadataFiles
from orchestra.canon.modules import discover
from orchestra.canon.schema import SchemaError
from orchestra.canon.types import get_object


def _check_snapshots(metadata: MetadataFiles) -> list[str]:
    installed = discover()
    if not installed:
        raise SchemaError("no installed Canon schema modules found")
    pins = get_object(metadata.load_config(), "schemas")
    if pins is None:
        raise StoreError("config.json schemas must be an object")
    snapshots = {path.stem for path in metadata.schemas_dir.glob("*.json")}
    failures = [
        f"{namespace}: schema is pinned or snapshotted but has no installed module"
        for namespace in sorted((pins.keys() | snapshots) - installed.keys())
    ]
    for namespace, module in sorted(installed.items()):
        snapshot_path = metadata.snapshot_path(namespace)
        snapshot = metadata.read_snapshot(namespace)
        if snapshot is None:
            failures.append(f"{namespace}: missing schema snapshot {snapshot_path}")
        elif snapshot != module.text:
            failures.append(
                f"{namespace}: stale schema snapshot {snapshot_path} differs from {module.source}"
            )

        if namespace not in pins:
            failures.append(f"{namespace}: missing schema pin in {metadata.config_path()}")
        elif pins[namespace] != module.version:
            failures.append(
                f"{namespace}: installed schema is {module.version}, "
                f"config.json pins {pins[namespace]}"
            )
    return failures


def main() -> int:
    try:
        failures = _check_snapshots(MetadataFiles(Path(".canon")))
    except (OSError, UnicodeError, StoreError, SchemaError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for failure in failures:
        print(failure, file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
