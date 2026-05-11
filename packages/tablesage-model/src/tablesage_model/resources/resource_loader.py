from __future__ import annotations

from enum import StrEnum
from importlib.resources import files
from typing import Final

RESOURCE_PACKAGE: Final[str] = __name__.rsplit(".", maxsplit=1)[0]


class ResourceDirectory(StrEnum):
    FRAGMENTS = "fragments"


def read_resource_text(directory: ResourceDirectory, filename: str, encoding: str = "utf-8") -> str:
    return files(RESOURCE_PACKAGE).joinpath(directory.value, filename).read_text(encoding)
