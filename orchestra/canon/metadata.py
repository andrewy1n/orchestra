"""Repository metadata files shared by the SQLite backend."""

from __future__ import annotations

import json
from pathlib import Path

from orchestra.canon.config import CONFIG_NAME, ConfigError, dump_config, validate_config
from orchestra.canon.errors import PartialStoreError, StoreError, StoreNotInitializedError
from orchestra.canon.types import JsonObject


class MetadataFiles:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.schemas_dir = root / "schemas"

    def config_path(self) -> Path:
        return self.root / CONFIG_NAME

    def snapshot_path(self, namespace: str) -> Path:
        return self.schemas_dir / f"{namespace}.json"

    def has_config(self) -> bool:
        return self.config_path().is_file()

    def is_absent(self) -> bool:
        return not self.root.exists() or not self.config_path().exists()

    def load_config(self) -> JsonObject:
        if not self.config_path().is_file():
            if self.root.exists() and any(self.root.iterdir()):
                raise PartialStoreError("store exists without valid config.json")
            raise StoreNotInitializedError("store not initialized")
        try:
            data = json.loads(self.config_path().read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise StoreError(f"malformed JSON in config.json: {exc}") from exc
        try:
            return validate_config(data)
        except ConfigError as exc:
            raise StoreError(str(exc)) from exc

    def write_config(self, config: JsonObject) -> None:
        try:
            validate_config(config)
        except ConfigError as exc:
            raise StoreError(str(exc)) from exc
        self._atomic_write(self.config_path(), dump_config(config))

    def write_snapshot(self, namespace: str, text: str) -> None:
        self._atomic_write(self.snapshot_path(namespace), text)

    def read_snapshot(self, namespace: str) -> str | None:
        path = self.snapshot_path(namespace)
        return path.read_text() if path.is_file() else None

    def _atomic_write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
