from __future__ import annotations

from shutil import which


def ensure_media_tools() -> None:
    """Fail before opening the TUI if required media executables are unavailable."""
    missing = [name for name in ("ffmpeg", "ffplay") if which(name) is None]
    if missing:
        raise SystemExit(
            f"TableSage requires {', '.join(missing)} on PATH.\n"
            "Install FFmpeg with both ffmpeg and ffplay:\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  macOS (Homebrew): brew install ffmpeg\n"
            "  Windows: install an FFmpeg build and add its bin directory to PATH.\n"
            "Downloads and platform instructions: https://ffmpeg.org/download.html\n"
            "Then restart your terminal and run tablesage-rpg again."
        )
