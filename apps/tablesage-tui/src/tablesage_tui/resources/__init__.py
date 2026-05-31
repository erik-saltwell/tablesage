from __future__ import annotations

from os import PathLike
from pathlib import Path

RESOURCE_DIRECTORY = Path(__file__).resolve().parent


def load_resource(filepath: str | PathLike[str], encoding: str = "utf-8") -> str:
    path = Path(filepath)
    if not path.is_absolute():
        path = RESOURCE_DIRECTORY / path

    return path.read_text(encoding=encoding)


__all__ = ["RESOURCE_DIRECTORY", "load_resource"]
