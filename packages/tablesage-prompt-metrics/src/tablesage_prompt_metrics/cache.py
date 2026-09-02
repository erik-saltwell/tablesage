from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class ContentCache:
    """Local content-addressed cache for transcript-derived judge artifacts."""

    def __init__(self, root: Path) -> None:
        self.root: Path = root.resolve()

    @staticmethod
    def key(*parts: object) -> str:
        encoded: bytes = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def load(self, namespace: str, key: str, model: type[ModelT]) -> ModelT | None:
        path: Path = self.root / namespace / f"{key}.json"
        if not path.is_file():
            return None
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, namespace: str, key: str, value: BaseModel) -> None:
        directory: Path = self.root / namespace
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{key}.json").write_text(value.model_dump_json(indent=2) + "\n", encoding="utf-8")
