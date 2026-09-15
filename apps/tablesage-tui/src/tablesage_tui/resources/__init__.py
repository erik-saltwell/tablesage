from __future__ import annotations

from os import PathLike
from pathlib import Path

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
ASCII_ART_DIRECTORY = RESOURCE_DIRECTORY / "ascii_art"


def load_resource(filepath: str | PathLike[str], encoding: str = "utf-8") -> str:
    path = Path(filepath)
    if not path.is_absolute():
        path = RESOURCE_DIRECTORY / path

    return path.read_text(encoding=encoding)


def load_ascii_art(filename: str | PathLike[str], encoding: str = "utf-8") -> str:
    """Load a bundled ASCII-art asset by its filename."""
    path = Path(filename)
    if path.is_absolute() or path.parent != Path("."):
        raise ValueError("ASCII art resources must be addressed by filename.")
    return (ASCII_ART_DIRECTORY / path).read_text(encoding=encoding)


__all__ = ["ASCII_ART_DIRECTORY", "RESOURCE_DIRECTORY", "load_ascii_art", "load_resource"]
