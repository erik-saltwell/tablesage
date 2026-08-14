from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from .. import _paths


def load_model_from_yaml[T: BaseModel](path: str | Path, model_type: type[T]) -> T:
    with open(path, encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty or blank YAML file: {path}")
    return model_type.model_validate(data)


def save_model_to_yaml(path: str | Path, model: BaseModel) -> None:
    path = Path(path)
    _paths.ensure_dir(path.parent)
    data: dict[str, Any] = model.model_dump(mode="json")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
        )
