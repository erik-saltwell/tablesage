from __future__ import annotations

import subprocess
from pathlib import Path


class ClipPlayer:
    """Fire-and-forget playback of a single audio clip via `ffplay`, one process at a time.

    `ffplay` ships alongside `ffmpeg`, already a hard dependency of this app (see
    `tablesage_tools.audio.ffmpeg`) -- no new dependency. Starting a new clip stops
    whatever was already playing, so clicking through a transcript never overlaps audio.
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None

    def play(self, path: Path) -> None:
        self.stop()
        self._process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
        self._process = None
