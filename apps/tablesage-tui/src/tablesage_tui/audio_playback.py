from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path

from textual.message_pump import MessagePump
from textual.timer import Timer


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


class PlaybackMode(Enum):
    MANUAL = "manual"
    AUTO = "auto"


_AUTO_ADVANCE_DELAY = 0.25


class ReviewPlayback:
    """Clip playback with an optional Auto mode that asks the screen to advance once a clip finishes.

    Shared by the review screens. The screen owns row navigation: `on_advance` moves to the next
    row (which plays it) and returns False when there is none, which drops back to Manual.
    """

    def __init__(self, timer_owner: MessagePump, on_advance: Callable[[], bool], on_mode_changed: Callable[[], None]) -> None:
        self._player = ClipPlayer()
        self._timer_owner = timer_owner
        self._on_advance = on_advance
        self._on_mode_changed = on_mode_changed
        self._timer: Timer | None = None
        self._started_at = 0.0
        self._duration = 0.0
        self.mode = PlaybackMode.MANUAL

    def play(self, clip: Path | None, duration: float) -> None:
        """Play `clip` (silently skipped when missing) and, in Auto, schedule the advance after `duration`."""
        self._started_at = time.monotonic()
        self._duration = max(0.0, duration)
        if clip is not None and clip.is_file():
            self._player.play(clip)
        else:
            self._player.stop()
        self._reschedule()

    def toggle_mode(self) -> None:
        self._set_mode(PlaybackMode.MANUAL if self.mode is PlaybackMode.AUTO else PlaybackMode.AUTO)
        self._reschedule()

    def set_manual(self) -> None:
        if self.mode is not PlaybackMode.MANUAL:
            self._set_mode(PlaybackMode.MANUAL)
        self._cancel_timer()

    def stop(self) -> None:
        self._player.stop()
        self._cancel_timer()

    def _set_mode(self, mode: PlaybackMode) -> None:
        self.mode = mode
        self._on_mode_changed()

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _reschedule(self) -> None:
        self._cancel_timer()
        if self.mode is not PlaybackMode.AUTO:
            return
        remaining = max(0.0, self._duration - (time.monotonic() - self._started_at)) + _AUTO_ADVANCE_DELAY
        self._timer = self._timer_owner.set_timer(remaining, self._advance_due)

    def _advance_due(self) -> None:
        self._timer = None
        if not self._on_advance():
            self.set_manual()
