"""Screen exports and compatibility with launchers installed before the CLI entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main_app import TableSageApp


def main() -> None:
    # An older editable installation may still import screens.main. Parse its command arguments
    # through the CLI too, without importing the TUI or performing startup work for diagnostics.
    from ..cli import main as run_cli

    run_cli()


def __getattr__(name: str) -> Any:
    if name == "TableSageApp":
        from .main_app import TableSageApp

        return TableSageApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TableSageApp", "main"]
