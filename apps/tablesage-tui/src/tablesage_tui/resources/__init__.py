from __future__ import annotations

from os import PathLike
from pathlib import Path

RESOURCE_DIRECTORY = Path(__file__).resolve().parent
ASCII_ART_DIRECTORY = RESOURCE_DIRECTORY / "ascii_art"
# The wheel bundles the repository's `docs/` here (see pyproject.toml); a source checkout reads `docs/` in place.
_BUNDLED_DOCS_DIRECTORY = RESOURCE_DIRECTORY / "docs"
_CHECKOUT_DOCS_DIRECTORY = RESOURCE_DIRECTORY.parents[4] / "docs"


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


def docs_directory() -> Path | None:
    """The public documentation served as help topics: bundled in an installed wheel, in place in a checkout."""
    for directory in (_BUNDLED_DOCS_DIRECTORY, _CHECKOUT_DOCS_DIRECTORY):
        if directory.is_dir():
            return directory
    return None


__all__ = ["ASCII_ART_DIRECTORY", "RESOURCE_DIRECTORY", "docs_directory", "load_ascii_art", "load_resource"]
